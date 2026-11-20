"""Use the Laya cross-encoder to choose between explicit criteria."""
from _common import arguments, base, mp, present, run


def main():
    args = arguments("Decision Maker", "laya_s256.task", text="Please help me find a book about astronomy.").parse_args()
    question = mp.tasks.decision.ChoiceQuestion(criteria={"library": "The user wants to find or borrow a book.", "weather": "The user wants a weather forecast."})
    with mp.tasks.decision.DecisionMaker.create_from_options(mp.tasks.decision.DecisionMakerOptions(base_options=base(args))) as task:
        result = task.evaluate_choice(args.text, question)
    return present(args, {"selected": result.selected_key, "probabilities": {k: round(v, 5) for k, v in result.probabilities.items()}}, text=args.text, criteria=question.criteria)


if __name__ == "__main__":
    run(main)
