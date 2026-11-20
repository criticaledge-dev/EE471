"""Summarize with Google's dedicated 200M task model."""
from _common import arguments, base, cache, mp, present, run


def main():
    text = "The city library opened a new reading room on Monday. The room has twenty desks and free internet. Students can use it from nine in the morning until six in the evening. The library hopes the quiet space will help students prepare for exams."
    args = arguments("Text Summarizer", "summarization_quant_200m_2modes.litertlm", text=text).parse_args()
    options = mp.tasks.text.TextSummarizerOptions(base_options=base(args), mode=mp.tasks.text.TextSummarizerMode.TLDR, max_num_tokens=512, cache_dir=cache("summarizer-cache"))
    with mp.tasks.text.TextSummarizer.create_from_options(options) as task:
        result = task.summarize(args.text)
    if not result.summary:
        raise RuntimeError("The model returned no summary.")
    return present(args, {"summary": result.summary}, text=args.text)


if __name__ == "__main__":
    run(main)
