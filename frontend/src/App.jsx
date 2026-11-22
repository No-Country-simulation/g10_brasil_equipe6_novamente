
import { useEffect, useState } from "react";
import UploadDocument from "./components/UploadDocument";
import ParametersPanel from "./components/ParametersPanel";
import ResultsPanel from "./components/ResultsPanel";

const OCI_HTTPS_BASE_URL = "https://137-131-213-187.sslip.io";

const RAW_API_URL = (
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV
    ? "http://localhost:8000/api/adaptar"
    : `${OCI_HTTPS_BASE_URL}/api/adaptar`)
)
  .trim()
  .replace(/\/+$/, "");

// Se estiver em produção ou se VITE_API_URL apontar para o IP HTTP da OCI, usa o domínio HTTPS direto da VM (sem limite de 4.5 MB da Vercel)
const RESOLVED_API_URL =
  RAW_API_URL.startsWith("http://137.131.213.187") ||
  RAW_API_URL === "/api/adaptar"
    ? `${OCI_HTTPS_BASE_URL}/api/adaptar`
    : RAW_API_URL;

const API_URL = RESOLVED_API_URL.endsWith("/api/adaptar")
  ? RESOLVED_API_URL
  : `${RESOLVED_API_URL}/api/adaptar`;

const API_PREPARAR_RAG_URL = API_URL.replace(/\/api\/adaptar$/, "/api/preparar-rag");
const API_FINALIZAR_LOCAL_URL = API_URL.replace(/\/api\/adaptar$/, "/api/finalizar-local");

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [resultData, setResultData] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [apiError, setApiError] = useState("");

  const [parameters, setParameters] = useState({
    engine: "Nuvem",
    localModel: "",
    apiKey: "",
    profile: "Iniciante",
    niche: "Geral",
    format: "Flashcards",
  });

  const [localModels, setLocalModels] = useState([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [ollamaError, setOllamaError] = useState("");

  const handleParameterChange = (field, value) => {
    setParameters((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  // Detecta os modelos instalados no Ollama
  useEffect(() => {
    if (parameters.engine !== "Local") return;

    const controller = new AbortController();

    const loadOllamaModels = async () => {
      setIsLoadingModels(true);
      setOllamaError("");
      setLocalModels([]);

      try {
        const response = await fetch(
          "http://localhost:11434/api/tags",
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error("Ollama indisponível");
        }

        const data = await response.json();
        const models = Array.isArray(data.models) ? data.models : [];

        if (models.length === 0) {
          throw new Error("Nenhum modelo encontrado");
        }

        setLocalModels(models);

        setParameters((previous) => ({
          ...previous,
          localModel: models.some(
            (model) => model.name === previous.localModel
          )
            ? previous.localModel
            : models[0].name,
        }));
      } catch (error) {
        if (error.name === "AbortError") return;

        setLocalModels([]);
        setParameters((previous) => ({
          ...previous,
          localModel: "",
        }));

        setOllamaError(
          typeof window !== "undefined" && window.location.protocol === "https:"
            ? 'Ollama local não detectado na porta 11434 ou bloqueado por CORS. Para usar o Ollama do seu PC em um site HTTPS, defina OLLAMA_ORIGINS="*" nas variáveis de ambiente da sua máquina e reinicie o Ollama.'
            : "Ollama não detectado na porta 11434 ou não há modelos carregados"
        );
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingModels(false);
        }
      }
    };

    loadOllamaModels();

    return () => controller.abort();
  }, [parameters.engine]);

  const canGenerate =
    selectedFile &&
    !isGenerating &&
    (parameters.engine === "Nuvem"
      ? parameters.apiKey.trim().length > 0
      : !isLoadingModels &&
        !ollamaError &&
        parameters.localModel.length > 0);

  // Envia o documento e os parâmetros para a API Python
  const handleGenerate = async () => {
    if (!canGenerate) return;

    setIsGenerating(true);
    setShowResults(false);
    setResultData(null);
    setApiError("");

    try {
      const formData = new FormData();

      formData.append("perfil", parameters.profile);
      formData.append("formato", parameters.format);
      formData.append("nicho", parameters.niche);
      formData.append("file", selectedFile);

      let data = null;

      if (parameters.engine === "Local") {
        // 1. Backend na OCI indexa o documento no RAG (ChromaDB) e devolve os prompts
        const ragResponse = await fetch(API_PREPARAR_RAG_URL, {
          method: "POST",
          body: formData,
        });
        const ragData = await ragResponse.json().catch(() => null);
        if (!ragResponse.ok) {
          throw new Error(
            typeof ragData?.detail === "string"
              ? ragData.detail
              : `Falha ao indexar documento no RAG (HTTP ${ragResponse.status}).`
          );
        }

        // 2. Navegador do visitante chama o Ollama instalado no próprio PC dele (localhost:11434)
        const ollamaResponse = await fetch("http://localhost:11434/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: parameters.localModel,
            messages: [
              { role: "system", content: ragData.system_prompt },
              { role: "user", content: ragData.user_prompt },
            ],
            format: "json",
            stream: false,
            options: {
              temperature: 0.3,
              repeat_penalty: 1.15,
              num_predict: 1200,
            },
          }),
        });
        const ollamaData = await ollamaResponse.json().catch(() => null);
        if (!ollamaResponse.ok || !ollamaData?.message?.content) {
          throw new Error(
            ollamaData?.error
              ? `Erro no Ollama local: ${ollamaData.error}`
              : "Falha ao gerar conteúdo no Ollama local da sua máquina (porta 11434)."
          );
        }

        // 3. Backend na OCI valida/normaliza o JSON (SaidaLLM) e salva a evidência no Bucket da OCI
        const finalResponse = await fetch(API_FINALIZAR_LOCAL_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nome_ficheiro: ragData.nome_ficheiro || selectedFile.name,
            perfil: parameters.profile,
            formato: parameters.format,
            nicho: parameters.niche,
            resposta_bruta: ollamaData.message.content,
          }),
        });
        data = await finalResponse.json().catch(() => null);
        if (!finalResponse.ok) {
          throw new Error(
            typeof data?.detail === "string"
              ? data.detail
              : `O modelo local não retornou um conteúdo válido (HTTP ${finalResponse.status}).`
          );
        }
      } else {
        formData.append("motor", "Nuvem (Google Gemini)");
        formData.append("modelo_local", "");
        formData.append("apiKey", parameters.apiKey);

        const response = await fetch(API_URL, {
          method: "POST",
          body: formData,
        });

        data = await response.json().catch(() => null);

        if (!response.ok) {
          const detail = data?.detail;

          if (typeof detail === "string" && detail.trim()) {
            throw new Error(detail);
          }
          if (response.status === 413) {
            throw new Error(
              "O arquivo enviado excede o limite de 4.5 MB do proxy gratuito da Vercel. Envie um PDF/TXT/MD menor que 4.5 MB."
            );
          }
          if (response.status === 404) {
            throw new Error(
              "Rota /api/adaptar não encontrada (404). Verifique se o commit com frontend/vercel.json já foi enviado (git push) e publicado na Vercel."
            );
          }
          if (response.status === 504 || response.status === 502) {
            throw new Error(
              `Tempo limite do proxy da Vercel excedido (HTTP ${response.status}). Tente com um documento menor.`
            );
          }
          throw new Error(
            `O servidor não conseguiu processar o documento (HTTP ${response.status}).`
          );
        }
      }

      if (!data?.conteudo_adaptado) {
        throw new Error(
          "A resposta da API não contém o conteúdo adaptado esperado."
        );
      }

      setResultData(data);
      setShowResults(true);
    } catch (error) {
      console.error("Erro ao gerar conteúdo:", error);

      setApiError(
        error.message === "Failed to fetch"
          ? "Não foi possível conectar ao servidor. Verifique se o backend Python está em execução."
          : error.message
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0e1117] px-4 py-8 text-white sm:px-6 sm:py-12">
      <div className="mx-auto max-w-5xl space-y-10">

        <header className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-600 text-2xl shadow-lg shadow-purple-900/30">
              🧠
            </div>

            <h1 className="text-3xl font-bold tracking-tight">
              NovaMente
            </h1>
          </div>

          <h2 className="text-xl font-semibold text-purple-300 sm:text-2xl">
            Adaptação Inteligente de Conteúdo Técnico
          </h2>

          <p className="max-w-2xl text-sm leading-relaxed text-zinc-400 sm:text-base">
            Transforme documentos técnicos em experiências de aprendizagem
            personalizadas. Escolha seu perfil, contexto e formato de estudo.
          </p>
        </header>

        <UploadDocument onFileSelect={setSelectedFile} />

        <ParametersPanel
          parameters={parameters}
          onParameterChange={handleParameterChange}
          localModels={localModels}
          isLoadingModels={isLoadingModels}
          ollamaError={ollamaError}
        />

        <div className="flex flex-col items-end gap-2">
          <button
            type="button"
            disabled={!canGenerate}
            onClick={handleGenerate}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 px-6 py-4 font-semibold text-white shadow-lg shadow-purple-900/20 transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto"
          >
            {isGenerating
              ? "Gerando seu material..."
              : "✨ Gerar conteúdo educacional"}
          </button>

          {!selectedFile && (
            <p className="text-xs text-zinc-500">
              Selecione um documento para liberar a geração.
            </p>
          )}

          {parameters.engine === "Nuvem" &&
            !parameters.apiKey.trim() && (
              <p className="text-xs text-zinc-500">
                Informe sua API Key do Gemini para continuar.
              </p>
            )}

          {parameters.engine === "Local" &&
            isLoadingModels && (
              <p className="text-xs text-zinc-400">
                Procurando modelos instalados no Ollama...
              </p>
            )}
        </div>

        {apiError && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {apiError}
          </div>
        )}

        {showResults && resultData && (
          <ResultsPanel
            parameters={parameters}
            resultData={resultData}
          />
        )}

        <footer className="border-t border-zinc-800 pt-6 text-center text-xs text-zinc-500">
          NovaMente · Aprendizagem inteligente e personalizada
        </footer>

      </div>
    </main>
  );
}

export default App;
