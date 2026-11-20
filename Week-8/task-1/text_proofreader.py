"""Run the official Proofread 200M model; no rule-based replacement."""
from _common import arguments, base, cache, mp, present, run


def main():
    args = arguments("Text Proofreader", "proofread_quant_200m.litertlm", text="Their are severel typos in this sentance.").parse_args()
    options = mp.tasks.text.TextProofreaderOptions(base_options=base(args), max_num_tokens=512, cache_dir=cache("proofreader-cache"))
    with mp.tasks.text.TextProofreader.create_from_options(options) as task:
        result = task.proofread(args.text)
    if not result.proofread_text:
        raise RuntimeError("The model returned no corrected text.")
    return present(args, {"input": args.text, "proofread_text": result.proofread_text}, text=args.text)


if __name__ == "__main__":
    run(main)
