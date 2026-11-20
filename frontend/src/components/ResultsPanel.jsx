
import { useState } from "react";

function ResultsPanel({ parameters = {}, resultData }) {
  const [copied, setCopied] = useState(false);

  const adaptedContent = resultData?.conteudo_adaptado;
  const metadata = resultData?.metadados ?? {};

  const content = {
    titulo: adaptedContent?.titulo ?? "Conteúdo adaptado",
    introducao:
      adaptedContent?.introducao_contextualizada ??
      "Não foi fornecida uma introdução para este conteúdo.",
    conceitos: Array.isArray(metadata.conceitos_chave)
      ? metadata.conceitos_chave
      : [],
    itens: Array.isArray(adaptedContent?.itens)
      ? adaptedContent.itens.map((item) => ({
          pergunta: item.topico_ou_pergunta ?? "Tópico",
          resposta:
            item.explicacao_ou_resposta ?? "Sem explicação disponível.",
        }))
      : [],
  };

  const format =
    metadata.formato_gerado ?? parameters.format ?? "Flashcards";

  const profile =
    metadata.perfil_aplicado ?? parameters.profile ?? "Não informado";

  const niche = parameters.niche ?? "Geral";

  const studyTime =
    metadata.tempo_estimado_estudo_minutos ?? 0;

  const handleCopy = async () => {
    const text = [
      content.titulo,
      `Perfil: ${profile}`,
      `Nicho: ${niche}`,
      `Formato: ${format}`,
      content.introducao,
      "Conceitos-chave:",
      ...content.conceitos,
      ...content.itens.map(
        (item) => `${item.pergunta}\n${item.resposta}`
      ),
    ].join("\n\n");

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      alert("Não foi possível copiar o conteúdo.");
    }
  };

  const renderStudyContent = () => {
    if (format === "Flashcards") {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">
            Flashcards para estudar
          </h3>

          {content.itens.map((item, index) => (
            <article
              key={index}
              className="rounded-xl border border-zinc-800 bg-zinc-800/40 p-5"
            >
              <span className="text-xs font-semibold text-purple-400">
                CARTÃO {index + 1}
              </span>

              <h4 className="mt-3 whitespace-pre-line font-semibold text-white">
                {item.pergunta}
              </h4>

              <p className="mt-3 whitespace-pre-line text-sm leading-7 text-zinc-300">
                {item.resposta}
              </p>
            </article>
          ))}
        </div>
      );
    }

    if (format === "Tutorial Passo a Passo") {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">
            Tutorial Passo a Passo
          </h3>

          {content.itens.map((item, index) => (
            <article
              key={index}
              className="flex gap-4 rounded-xl border border-zinc-800 bg-zinc-800/40 p-5"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-purple-600/20 font-bold text-purple-300">
                {index + 1}
              </div>

              <div>
                <h4 className="whitespace-pre-line font-semibold text-white">
                  {item.pergunta}
                </h4>

                <p className="mt-2 whitespace-pre-line text-sm leading-7 text-zinc-300">
                  {item.resposta}
                </p>
              </div>
            </article>
          ))}
        </div>
      );
    }

    if (format === "Quiz") {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">
            Quiz — Teste seus conhecimentos
          </h3>

          {content.itens.map((item, index) => (
            <article
              key={index}
              className="rounded-xl border border-zinc-800 bg-zinc-800/40 p-5"
            >
              <span className="text-xs font-semibold text-purple-400">
                PERGUNTA {index + 1}
              </span>

              <h4 className="mt-3 whitespace-pre-line font-semibold text-white">
                {item.pergunta}
              </h4>

              <div className="mt-4 rounded-lg bg-purple-500/10 p-4">
                <p className="text-xs font-semibold text-purple-300">
                  RESPOSTA / EXPLICAÇÃO
                </p>

                <p className="mt-2 whitespace-pre-line text-sm leading-7 text-zinc-300">
                  {item.resposta}
                </p>
              </div>
            </article>
          ))}
        </div>
      );
    }

    if (format === "Resumo Executivo") {
      return (
        <div className="space-y-5 rounded-xl border border-zinc-800 bg-zinc-800/40 p-5">
          <h3 className="text-lg font-semibold text-white">
            Resumo Executivo
          </h3>

          <p className="text-sm leading-7 text-zinc-300">
            {content.introducao}
          </p>

          <h4 className="font-semibold text-white">
            Principais pontos
          </h4>

          <ul className="space-y-4">
            {content.itens.map((item, index) => (
              <li
                key={index}
                className="border-l-2 border-purple-500 pl-4"
              >
                <p className="font-medium text-white">
                  {item.pergunta}
                </p>

                <p className="mt-1 text-sm leading-6 text-zinc-400">
                  {item.resposta}
                </p>
              </li>
            ))}
          </ul>
        </div>
      );
    }

    return (
      <p className="text-sm text-zinc-400">
        Formato não reconhecido: {format}
      </p>
    );
  };

  return (
    <section className="space-y-6 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5 sm:p-7">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xl">✨</span>

            <span className="text-sm font-semibold text-purple-400">
              CONTEÚDO ADAPTADO
            </span>
          </div>

          <h2 className="text-2xl font-bold text-white">
            {content.titulo}
          </h2>

          <p className="mt-2 text-sm text-zinc-400">
            Material educacional personalizado para seu aprendizado.
          </p>
        </div>

        <span className="w-fit rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
          Resultado da IA
        </span>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-800/60 p-4">
          <p className="text-xs text-zinc-400">Perfil aplicado</p>
          <p className="mt-1 font-semibold text-white">{profile}</p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-800/60 p-4">
          <p className="text-xs text-zinc-400">Nicho de aplicação</p>
          <p className="mt-1 font-semibold text-white">{niche}</p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-800/60 p-4">
          <p className="text-xs text-zinc-400">Tempo estimado</p>
          <p className="mt-1 font-semibold text-white">
            {studyTime} minutos
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-white">
          Sobre este conteúdo
        </h3>

        <p className="rounded-xl border border-zinc-800 bg-zinc-800/40 p-4 text-sm leading-7 text-zinc-300">
          {content.introducao}
        </p>
      </div>

      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-white">
          Conceitos-chave
        </h3>

        <div className="flex flex-wrap gap-2">
          {content.conceitos.map((concept, index) => (
            <span
              key={index}
              className="rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-2 text-xs font-medium text-purple-300"
            >
              {concept}
            </span>
          ))}
        </div>
      </div>

      {renderStudyContent()}

      <div className="flex justify-end border-t border-zinc-800 pt-5">
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-xl border border-zinc-700 px-5 py-3 text-sm font-medium text-zinc-200 transition hover:border-purple-500 hover:bg-zinc-800"
        >
          {copied ? "✓ Conteúdo copiado!" : "Copiar conteúdo"}
        </button>
      </div>
    </section>
  );
}

export default ResultsPanel;
