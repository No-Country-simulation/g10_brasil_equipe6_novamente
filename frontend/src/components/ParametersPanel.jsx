
function ParametersPanel({
  parameters,
  onParameterChange,
  localModels = [],
  isLoadingModels = false,
  ollamaError = "",
}) {
  const selectClass =
    "mt-2 w-full rounded-xl border border-zinc-700 bg-zinc-800 px-4 py-3 text-sm text-white outline-none transition focus:border-purple-500";

  const labelClass = "text-sm font-medium text-zinc-200";

  return (
    <section className="w-full space-y-5 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5 sm:p-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xl">⚙️</span>
          <h2 className="text-lg font-semibold text-white">
            Personalize seu aprendizado
          </h2>
        </div>

        <p className="mt-2 text-sm text-zinc-400">
          Configure como a inteligência artificial deve adaptar seu conteúdo.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Mecanismo de IA</label>
          <select
            className={selectClass}
            value={parameters.engine}
            onChange={(event) =>
              onParameterChange("engine", event.target.value)
            }
          >
            <option value="Nuvem">Nuvem — Google Gemini</option>
            <option value="Local">Local — Ollama</option>
          </select>
        </div>

        {parameters.engine === "Nuvem" && (
          <div>
            <label className={labelClass}>API Key do Google Gemini</label>
            <input
              type="password"
              autoComplete="off"
              placeholder="Insira sua API Key"
              value={parameters.apiKey ?? ""}
              onChange={(event) =>
                onParameterChange("apiKey", event.target.value)
              }
              className={selectClass}
            />
            <p className="mt-2 text-xs text-zinc-500">
              Sua chave será utilizada para realizar as requisições ao Gemini.
            </p>
          </div>
        )}

        {parameters.engine === "Local" && (
          <div>
            <label className={labelClass}>Modelo local (Ollama)</label>
            <select
              className={selectClass}
              value={parameters.localModel ?? ""}
              disabled={isLoadingModels || localModels.length === 0}
              onChange={(event) =>
                onParameterChange("localModel", event.target.value)
              }
            >
              {isLoadingModels ? (
                <option value="">Detectando modelos...</option>
              ) : localModels.length > 0 ? (
                localModels.map((model) => {
                  const hasVision =
                    Array.isArray(model.capabilities) &&
                    model.capabilities.includes("vision");
                  return (
                    <option key={model.name} value={model.name}>
                      {model.name}
                      {hasVision ? " (👁️ Visão Multimodal)" : ""}
                    </option>
                  );
                })
              ) : (
                <option value="">Nenhum modelo encontrado</option>
              )}
            </select>

            {ollamaError && (
              <p className="mt-2 text-xs text-red-400">
                {ollamaError}
              </p>
            )}
          </div>
        )}

        <div>
          <label className={labelClass}>Perfil do público</label>
          <select
            className={selectClass}
            value={parameters.profile}
            onChange={(event) =>
              onParameterChange("profile", event.target.value)
            }
          >
            <option>Iniciante</option>
            <option>Dev Júnior / Pleno</option>
            <option>Líder Técnico / Arquiteto</option>
            <option>Gestor / Executivo</option>
          </select>
        </div>

        <div>
          <label className={labelClass}>Nicho de aplicação</label>
          <select
            className={selectClass}
            value={parameters.niche}
            onChange={(event) =>
              onParameterChange("niche", event.target.value)
            }
          >
            <option>Geral</option>
            <option>Fintech</option>
            <option>Saúde</option>
            <option>E-commerce</option>
          </select>
        </div>

        <div className="sm:col-span-2">
          <label className={labelClass}>Formato educacional</label>
          <select
            className={selectClass}
            value={parameters.format}
            onChange={(event) =>
              onParameterChange("format", event.target.value)
            }
          >
            <option>Flashcards</option>
            <option>Tutorial Passo a Passo</option>
            <option>Quiz</option>
            <option>Resumo Executivo</option>
          </select>
        </div>
      </div>
    </section>
  );
}

export default ParametersPanel;