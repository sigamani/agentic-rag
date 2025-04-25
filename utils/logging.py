import wandb

def init_wandb(project_name="pr-convfinqa", run_name="01"):
    wandb.init(
        project=project_name,
        name=run_name,
        config={
            "architecture": "LoRA + Unsloth",
        },
    )

def log_metrics(phase, epoch, loss, accuracy, claude_score):
    wandb.log({
        f"{phase}/epoch": epoch,
        f"{phase}/loss": loss,
        f"{phase}/accuracy": accuracy,
        f"{phase}/claude_score": claude_score,
    })
