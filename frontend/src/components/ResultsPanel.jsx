import { useState } from "react";

function parseQuizQuestion(rawQuestion, rawAnswer) {
  const text = String(rawQuestion ?? "").trim();
  const ans = String(rawAnswer ?? "").trim();

  // Extrai alternativas A, B, C, D (suporta "A) ...", "A. ...", "A - ...", "(A) ...")
  const optionRegex = /(?:^|\n)\s*\(?([A-D])\)?[).:-]\s*(.+?)(?=(?:\n\s*\(?[A-D]\)?[).:-]\s+)|$)/gis;
  const options = [];
  let firstMatchIndex = -1;
  let match;

  while ((match = optionRegex.exec(text)) !== null) {
    if (firstMatchIndex === -1) {
      firstMatchIndex = match.index;
    }
    options.push({
      letter: match[1].toUpperCase(),
      label: match[2].trim(),
    });
  }

  // Fallback para alternativas na mesma linha ("... A) op1 B) op2 C) op3 D) op4")
  if (options.length < 2) {
    options.length = 0;
    firstMatchIndex = -1;
    const inlineRegex = /\b([A-D])\)\s*([^A-D]+?)(?=\s+\b[A-D]\)\s*|$)/g;
    while ((match = inlineRegex.exec(text)) !== null) {
      if (firstMatchIndex === -1) {
        firstMatchIndex = match.index;
      }
      options.push({
        letter: match[1].toUpperCase(),
        label: match[2].trim(),
      });
    }
  }

  const stem =
    firstMatchIndex > 0 ? text.slice(0, firstMatchIndex).trim() : text;

  // Identifica a letra correta na resposta/explicação
  let correctLetter = null;
  const patterns = [
    /(?:letra|alternativa|op[cç][aã]o|resposta)\s*(?:correta)?\s*[:=-]?\s*\(?([A-D])\)?(?![a-zA-Z])/i,
    /^\s*\(?([A-D])\)?(?:[).:-]|\s+[-—–]|\s*$)/i,
    /\bcorreta\s+(?:[eé]\s+)?(?:a\s+)?(?:letra\s+|alternativa\s+)?\(?([A-D])\)?\b/i,
  ];

  for (const pat of patterns) {
    const m = ans.match(pat);
    if (m) {
      correctLetter = m[1].toUpperCase();
      break;
    }
  }

  return {
    stem: stem || text,
    options: options.length >= 2 ? options : [],
    correctLetter,
    explanation: ans,
  };
}

function slugify(value) {
  return String(value || "conteudo_novamente")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function downloadBlob(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function ResultsPanel({ parameters = {}, resultData }) {
  const [copied, setCopied] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [revealedQuestions, setRevealedQuestions] = useState({});
  const [flippedCards, setFlippedCards] = useState({});
  const [allCardsRevealed, setAllCardsRevealed] = useState(false);

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

  const studyTime = metadata.tempo_estimado_estudo_minutos ?? 0;

  const pipelineAgents =
    Array.isArray(metadata.pipeline_multiagente) &&
    metadata.pipeline_multiagente.length > 0
      ? metadata.pipeline_multiagente
      : [
          "Agente Pesquisador RAG",
          "Agente Redator Pedagógico",
          "Agente Crítico / Revisor",
        ];

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

  // --- Exportação 1: Markdown (.md) ---
  const handleDownloadMarkdown = () => {
    const mdLines = [
      `# ${content.titulo}`,
      "",
      `> **Perfil:** ${profile} | **Nicho:** ${niche} | **Formato:** ${format} | **Tempo estimado:** ${studyTime} min`,
      "",
      "## Contextualização",
      content.introducao,
      "",
      "## Conceitos-Chave",
      content.conceitos.map((c) => `- \`${c}\``).join("\n"),
      "",
      `## ${format}`,
      "",
      ...content.itens.map(
        (item, idx) =>
          `### ${idx + 1}. ${item.pergunta}\n\n${item.resposta}\n`
      ),
      "---",
      "*Gerado por NovaMente — Orquestração Multi-Agentes com LangGraph & RAG*",
    ];

    downloadBlob(
      `${slugify(content.titulo)}.md`,
      mdLines.join("\n"),
      "text/markdown;charset=utf-8"
    );
  };

  // --- Exportação 2: CSV compatível com Anki (.csv) ---
  const handleDownloadAnkiCsv = () => {
    const escapeCsv = (val) =>
      `"${String(val ?? "")
        .replace(/"/g, '""')
        .replace(/\r?\n/g, "<br>")}"`;

    const tag = `novamente ${slugify(profile)} ${slugify(niche)} ${slugify(format)}`;
    const rows = [
      "#separator:Semicolon",
      "#html:true",
      "#tags column:3",
      ...content.itens.map(
        (item) =>
          `${escapeCsv(item.pergunta)};${escapeCsv(item.resposta)};${escapeCsv(tag)}`
      ),
    ];

    // BOM UTF-8 (\uFEFF) para garantir acentuação perfeita no Anki / Excel
    downloadBlob(
      `${slugify(content.titulo)}_anki.csv`,
      "\uFEFF" + rows.join("\n"),
      "text/csv;charset=utf-8"
    );
  };

  // --- Exportação 3: PDF Didático Formatado ---
  const handleExportPdf = () => {
    const printWindow = window.open("", "_blank", "width=900,height=750");
    if (!printWindow) {
      alert(
        "Permita pop-ups no navegador para abrir a versão de impressão/PDF didático."
      );
      return;
    }

    const itemsHtml = content.itens
      .map(
        (item, idx) => `
        <div class="item">
          <div class="item-header">${idx + 1}. ${escapeHtml(item.pergunta).replace(/\n/g, "<br>")}</div>
          <div class="item-body">${escapeHtml(item.resposta).replace(/\n/g, "<br>")}</div>
        </div>`
      )
      .join("");

    const conceptsHtml = content.conceitos
      .map((c) => `<span class="badge">${escapeHtml(c)}</span>`)
      .join(" ");

    const htmlDoc = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>${escapeHtml(content.titulo)} — NovaMente</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #18181b;
      line-height: 1.6;
      padding: 36px 48px;
      max-width: 860px;
      margin: 0 auto;
    }
    .header {
      border-bottom: 3px solid #7c3aed;
      padding-bottom: 16px;
      margin-bottom: 22px;
    }
    .brand {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #7c3aed;
    }
    h1 {
      font-size: 24px;
      margin: 6px 0 10px 0;
      color: #111827;
    }
    .meta-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      font-size: 13px;
      background: #f4f4f5;
      padding: 10px 14px;
      border-radius: 8px;
      margin-bottom: 20px;
    }
    h2 {
      font-size: 16px;
      color: #4c1d95;
      margin-top: 22px;
      margin-bottom: 8px;
    }
    .intro {
      background: #faf5ff;
      border-left: 4px solid #7c3aed;
      padding: 12px 16px;
      border-radius: 6px;
      font-size: 14px;
    }
    .badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 10px 0 20px 0;
    }
    .badge {
      background: #ede9fe;
      color: #5b21b6;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 999px;
    }
    .item {
      border: 1px solid #e4e4e7;
      border-radius: 10px;
      padding: 14px 18px;
      margin-bottom: 14px;
      page-break-inside: avoid;
    }
    .item-header {
      font-weight: 700;
      font-size: 15px;
      color: #111827;
      margin-bottom: 8px;
    }
    .item-body {
      font-size: 14px;
      color: #3f3f46;
      background: #fafafa;
      padding: 10px 12px;
      border-radius: 6px;
    }
    footer {
      margin-top: 32px;
      padding-top: 12px;
      border-top: 1px solid #e4e4e7;
      font-size: 11px;
      color: #71717a;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="brand">🧠 NovaMente · Material Didático Adaptado</div>
    <h1>${escapeHtml(content.titulo)}</h1>
  </div>
  <div class="meta-grid">
    <div><strong>Perfil:</strong> ${escapeHtml(profile)}</div>
    <div><strong>Nicho:</strong> ${escapeHtml(niche)}</div>
    <div><strong>Formato:</strong> ${escapeHtml(format)}</div>
    <div><strong>Tempo estimado:</strong> ${escapeHtml(studyTime)} min</div>
  </div>
  <h2>Contextualização</h2>
  <div class="intro">${escapeHtml(content.introducao)}</div>
  <h2>Conceitos-Chave</h2>
  <div class="badges">${conceptsHtml}</div>
  <h2>${escapeHtml(format)}</h2>
  ${itemsHtml}
  <footer>
    Gerado por NovaMente · Orquestração Multi-Agentes com LangGraph (${escapeHtml(pipelineAgents.join(" → "))})
  </footer>
  <script>
    window.onload = function() {
      setTimeout(function() { window.print(); }, 250);
    };
  </script>
</body>
</html>`;

    printWindow.document.open();
    printWindow.document.write(htmlDoc);
    printWindow.document.close();
  };

  const renderStudyContent = () => {
    if (format === "Flashcards") {
      return (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-lg font-semibold text-white">
              Flashcards para estudo ativo
            </h3>
            <button
              type="button"
              onClick={() => setAllCardsRevealed((prev) => !prev)}
              className="rounded-lg border border-purple-500/40 bg-purple-500/10 px-3 py-1.5 text-xs font-medium text-purple-300 transition hover:bg-purple-500/20"
            >
              {allCardsRevealed
                ? "🙈 Ocultar todas as respostas"
                : "👁️ Revelar todas as respostas"}
            </button>
          </div>

          {content.itens.map((item, index) => {
            const isRevealed = allCardsRevealed || Boolean(flippedCards[index]);
            return (
              <article
                key={index}
                className="rounded-xl border border-zinc-800 bg-zinc-800/40 p-5 transition hover:border-zinc-700"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-purple-400">
                    CARTÃO {index + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() =>
                      setFlippedCards((prev) => ({
                        ...prev,
                        [index]: !prev[index],
                      }))
                    }
                    className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1 text-xs font-medium text-zinc-300 transition hover:border-purple-500 hover:text-white"
                  >
                    {isRevealed ? "🙈 Ocultar verso" : "🔄 Virar cartão (Ver resposta)"}
                  </button>
                </div>

                <h4 className="mt-3 whitespace-pre-line font-semibold text-white">
                  {item.pergunta}
                </h4>

                {isRevealed ? (
                  <div className="mt-4 rounded-lg border border-purple-500/20 bg-purple-500/10 p-4">
                    <p className="text-xs font-semibold text-purple-300">
                      VERSO (RESPOSTA)
                    </p>
                    <p className="mt-2 whitespace-pre-line text-sm leading-7 text-zinc-200">
                      {item.resposta}
                    </p>
                  </div>
                ) : (
                  <p className="mt-3 text-xs italic text-zinc-500">
                    Tente recordar a resposta e clique em &ldquo;Virar cartão&rdquo; para conferir.
                  </p>
                )}
              </article>
            );
          })}
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
      const parsedQuestions = content.itens.map((item) =>
        parseQuizQuestion(item.pergunta, item.resposta)
      );

      const totalQuestions = parsedQuestions.length;
      const answeredIndices = Object.keys(quizAnswers);
      const answeredCount = answeredIndices.length;
      const correctCount = answeredIndices.filter(
        (idx) => quizAnswers[idx]?.isCorrect
      ).length;
      const accuracy =
        answeredCount > 0
          ? Math.round((correctCount / answeredCount) * 100)
          : 0;

      const handleSelectOption = (qIndex, selectedLetter, correctLetter) => {
        const isCorrect =
          correctLetter ? selectedLetter === correctLetter : true;
        setQuizAnswers((prev) => ({
          ...prev,
          [qIndex]: {
            selected: selectedLetter,
            isCorrect,
          },
        }));
      };

      const handleResetQuiz = () => {
        setQuizAnswers({});
        setRevealedQuestions({});
      };

      return (
        <div className="space-y-5">
          <div className="flex flex-col justify-between gap-4 rounded-xl border border-purple-500/30 bg-purple-950/20 p-4 sm:flex-row sm:items-center">
            <div>
              <h3 className="text-lg font-semibold text-white">
                🎯 Quiz Interativo — Avaliação em Tempo Real
              </h3>
              <p className="mt-1 text-xs text-zinc-300">
                Selecione uma alternativa em cada questão para receber correção e feedback explicativo imediato.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-lg border border-zinc-700 bg-zinc-900/90 px-3 py-2 text-xs">
                <span className="text-zinc-400">Respondidas: </span>
                <strong className="text-white">
                  {answeredCount}/{totalQuestions}
                </strong>
              </div>
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs">
                <span className="text-emerald-300">Acertos: </span>
                <strong className="text-emerald-200">
                  {correctCount} ({accuracy}%)
                </strong>
              </div>
              {answeredCount > 0 && (
                <button
                  type="button"
                  onClick={handleResetQuiz}
                  className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs font-medium text-zinc-200 transition hover:border-purple-500"
                >
                  🔄 Refazer Quiz
                </button>
              )}
            </div>
          </div>

          {parsedQuestions.map((q, index) => {
            const answerState = quizAnswers[index];
            const isAnswered = Boolean(answerState);
            const isRevealed = Boolean(revealedQuestions[index]);

            return (
              <article
                key={index}
                className="rounded-xl border border-zinc-800 bg-zinc-800/40 p-5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-purple-400">
                    PERGUNTA {index + 1}
                  </span>
                  {isAnswered && (
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        answerState.isCorrect
                          ? "border border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
                          : "border border-red-500/40 bg-red-500/15 text-red-300"
                      }`}
                    >
                      {answerState.isCorrect
                        ? "✅ Resposta Correta!"
                        : `❌ Incorreta${q.correctLetter ? ` (Correta: ${q.correctLetter})` : ""}`}
                    </span>
                  )}
                </div>

                <h4 className="mt-3 whitespace-pre-line font-semibold text-white">
                  {q.stem}
                </h4>

                {q.options.length >= 2 ? (
                  <div className="mt-4 space-y-2.5">
                    {q.options.map((opt) => {
                      const isSelected =
                        answerState?.selected === opt.letter;
                      const isRightOption =
                        q.correctLetter === opt.letter;

                      let btnStyle =
                        "border-zinc-700 bg-zinc-900/70 text-zinc-200 hover:border-purple-500 hover:bg-zinc-800";

                      if (isAnswered) {
                        if (isRightOption) {
                          btnStyle =
                            "border-emerald-500 bg-emerald-500/15 text-emerald-100";
                        } else if (isSelected && !answerState.isCorrect) {
                          btnStyle =
                            "border-red-500 bg-red-500/15 text-red-200";
                        } else {
                          btnStyle =
                            "border-zinc-800 bg-zinc-900/40 text-zinc-400 opacity-75";
                        }
                      }

                      return (
                        <button
                          key={opt.letter}
                          type="button"
                          onClick={() =>
                            handleSelectOption(
                              index,
                              opt.letter,
                              q.correctLetter
                            )
                          }
                          className={`flex w-full items-start gap-3 rounded-xl border p-3.5 text-left text-sm transition ${btnStyle}`}
                        >
                          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-zinc-800 text-xs font-bold text-purple-300">
                            {opt.letter}
                          </span>
                          <span className="flex-1 leading-6">
                            {opt.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {!isRevealed ? (
                      <button
                        type="button"
                        onClick={() =>
                          setRevealedQuestions((prev) => ({
                            ...prev,
                            [index]: true,
                          }))
                        }
                        className="rounded-lg border border-purple-500/40 bg-purple-500/10 px-4 py-2 text-xs font-medium text-purple-300 transition hover:bg-purple-500/20"
                      >
                        👁️ Ver Resposta e Explicação
                      </button>
                    ) : (
                      !isAnswered && (
                        <>
                          <button
                            type="button"
                            onClick={() =>
                              setQuizAnswers((prev) => ({
                                ...prev,
                                [index]: { selected: "OK", isCorrect: true },
                              }))
                            }
                            className="rounded-lg border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-xs font-medium text-emerald-300"
                          >
                            ✅ Acertei
                          </button>
                          <button
                            type="button"
                            onClick={() =>
                              setQuizAnswers((prev) => ({
                                ...prev,
                                [index]: { selected: "ERR", isCorrect: false },
                              }))
                            }
                            className="rounded-lg border border-red-500/40 bg-red-500/15 px-3 py-1.5 text-xs font-medium text-red-300"
                          >
                            ❌ Preciso revisar
                          </button>
                        </>
                      )
                    )}
                  </div>
                )}

                {(isAnswered || isRevealed) && (
                  <div className="mt-4 rounded-lg border border-purple-500/20 bg-purple-500/10 p-4">
                    <p className="text-xs font-semibold text-purple-300">
                      FEEDBACK EXPLICATIVO
                    </p>
                    <p className="mt-2 whitespace-pre-line text-sm leading-7 text-zinc-200">
                      {q.explanation}
                    </p>
                  </div>
                )}
              </article>
            );
          })}
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
           Validado via LangGraph Multi-Agentes
        </span>
      </div>

      {/* Pipeline Multi-Agentes LangGraph */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/90 p-3.5">
        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          🤖 Pipeline Multi-Agentes (LangGraph)
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {pipelineAgents.map((agent, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <span className="rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-medium text-purple-200">
                ✓ {agent}
              </span>
              {idx < pipelineAgents.length - 1 && (
                <span className="text-xs text-zinc-500">→</span>
              )}
            </div>
          ))}
        </div>
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

      {/* Barra de Exportação Multiformato */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-zinc-800 pt-5">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleDownloadMarkdown}
            className="rounded-xl border border-zinc-700 bg-zinc-800/80 px-4 py-2.5 text-xs font-medium text-zinc-200 transition hover:border-purple-500 hover:bg-zinc-800"
          >
            📝 Baixar Markdown (.md)
          </button>

          <button
            type="button"
            onClick={handleDownloadAnkiCsv}
            className="rounded-xl border border-zinc-700 bg-zinc-800/80 px-4 py-2.5 text-xs font-medium text-zinc-200 transition hover:border-purple-500 hover:bg-zinc-800"
          >
            🗂️ Exportar Anki (.csv)
          </button>

          <button
            type="button"
            onClick={handleExportPdf}
            className="rounded-xl border border-zinc-700 bg-zinc-800/80 px-4 py-2.5 text-xs font-medium text-zinc-200 transition hover:border-purple-500 hover:bg-zinc-800"
          >
            📄 Exportar PDF Didático
          </button>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="rounded-xl border border-purple-500/40 bg-purple-600/20 px-5 py-2.5 text-xs font-semibold text-purple-200 transition hover:border-purple-400 hover:bg-purple-600/30"
        >
          {copied ? "✓ Conteúdo copiado!" : "📋 Copiar conteúdo"}
        </button>
      </div>
    </section>
  );
}

export default ResultsPanel;
