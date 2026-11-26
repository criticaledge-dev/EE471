"""Lazy, local text and image inference."""
from threading import Lock

CHAT_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
IMAGE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
CHAT_INSTRUCTIONS = (
    "Answer the last user message. For a new image prompt, write one vivid English sentence. "
    "When asked to edit a previous image prompt, make the requested change and keep the other details. "
    "If the user cancels or changes the subject, respond conversationally."
)

# Demonstrate edits and a change of intent in the model's native chat format.
# These example turns are separate from the actual conversation.
CHAT_EXAMPLE = (
    {"role": "user", "content": "Write an image prompt for a fox in a forest."},
    {"role": "assistant", "content": "A red fox in a misty forest."},
    {"role": "user", "content": "Replace the fox with a deer."},
    {"role": "assistant", "content": "A deer in a misty forest."},
    {"role": "user", "content": "Add moonlight."},
    {"role": "assistant", "content": "A deer in a misty forest lit by moonlight."},
    {"role": "user", "content": "Paint it in oils."},
    {"role": "assistant", "content": "An oil painting of a deer in a misty forest lit by moonlight."},
    {"role": "user", "content": "Forget it."},
    {"role": "assistant", "content": "Okay, we can leave it there."},
)


class Generation:
    def __init__(self):
        self.lock = Lock()
        self.chat = None
        self.image = None

    def reply(self, messages):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        with self.lock, torch.inference_mode():
            if self.chat is None:
                tokenizer = AutoTokenizer.from_pretrained(CHAT_MODEL)
                model = AutoModelForCausalLM.from_pretrained(CHAT_MODEL, use_safetensors=True).eval()
                self.chat = tokenizer, model
            tokenizer, model = self.chat
            context = [
                {"role": "system", "content": CHAT_INSTRUCTIONS},
                *CHAT_EXAMPLE,
                *messages,
            ]
            encoded = tokenizer.apply_chat_template(
                context, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt"
            )
            output = model.generate(
                **encoded, max_new_tokens=96, do_sample=False, eos_token_id=tokenizer.eos_token_id
            )
            reply = tokenizer.decode(output[0, encoded["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            if not reply:
                raise ValueError("The chat model returned no text.")
            return reply

    def render(self, prompt):
        import torch
        from diffusers import StableDiffusionPipeline

        with self.lock, torch.inference_mode():
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if self.image is None:
                options = {"use_safetensors": True, "torch_dtype": torch.float32}
                if device == "cuda":
                    options.update(torch_dtype=torch.float16, variant="fp16")
                pipe = StableDiffusionPipeline.from_pretrained(IMAGE_MODEL, **options)
                self.image = pipe.to(device)
            return self.image(prompt, width=512, height=512, num_inference_steps=20).images[0]
