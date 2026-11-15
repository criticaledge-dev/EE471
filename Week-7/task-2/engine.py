"""Sample-weighted epoch metrics shared by training and independent evaluation."""
import torch


def run_epoch(model, loader, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    loss_sum, correct, count = 0.0, 0, 0
    criterion = torch.nn.CrossEntropyLoss()
    context = torch.enable_grad() if training else torch.inference_mode()
    with context:
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            if training:
                optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            if training:
                loss.backward()
                optimizer.step()
            size = labels.size(0)
            loss_sum += loss.item() * size
            correct += (logits.argmax(1) == labels).sum().item()
            count += size
    if not count:
        raise ValueError("Cannot evaluate an empty dataset.")
    return {"loss": loss_sum / count, "accuracy": correct / count, "samples": count}
