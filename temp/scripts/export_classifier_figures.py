"""
Export figures for the classifier report section.

The script reads training logs from the two main notebooks when possible and
uses the final test metrics extracted from the notebooks to create report-ready
PNG figures and CSV tables.

Run from the project root:
    python scripts/export_classifier_figures.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = {
    "VGG16+Inception+ViT": ROOT / "train files" / "VGG16+Inception+ViT.ipynb",
    "VGG16+Inception+ViT_v4": ROOT / "train files" / "VGG16+Inception+ViT_v4.ipynb",
}
OUT_DIR = ROOT / "report_assets" / "classifier"

CLASS_NAMES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]

BASELINE_TEST = {
    "model": "VGG16+Inception+ViT",
    "loss": 0.7857,
    "accuracy": 0.876,
    "macro_f1": 0.749,
}

FINAL_TEST = {
    "model": "VGG16+Inception+ViT_v4",
    "loss": 0.2256,
    "accuracy": 0.870,
    "macro_f1": 0.764,
}

FINAL_CLASS_REPORT = pd.DataFrame(
    [
        ["akiec", 0.71, 0.76, 0.73, 49],
        ["bcc", 0.76, 0.82, 0.79, 77],
        ["bkl", 0.70, 0.78, 0.74, 165],
        ["df", 0.77, 0.59, 0.67, 17],
        ["mel", 0.76, 0.63, 0.69, 167],
        ["nv", 0.93, 0.94, 0.94, 1006],
        ["vasc", 0.89, 0.73, 0.80, 22],
        ["macro avg", 0.79, 0.75, 0.76, 1503],
        ["weighted avg", 0.87, 0.87, 0.87, 1503],
    ],
    columns=["class", "precision", "recall", "f1_score", "support"],
)

FINAL_CONFUSION_MATRIX = pd.DataFrame(
    [
        [37, 4, 3, 1, 1, 3, 0],
        [2, 63, 6, 0, 3, 3, 0],
        [7, 3, 128, 0, 10, 17, 0],
        [0, 2, 1, 10, 0, 4, 0],
        [6, 1, 15, 0, 105, 39, 1],
        [0, 8, 28, 1, 20, 948, 1],
        [0, 2, 1, 1, 0, 2, 16],
    ],
    index=CLASS_NAMES,
    columns=CLASS_NAMES,
)


LOG_PATTERN = re.compile(
    r"\[(?P<phase>[^\]]+)\]\[Epoch (?P<epoch>\d+)/(?:\d+)\]\s+"
    r"Train Loss: (?P<train_loss>\d+\.\d+)\s+\|\s+"
    r"Train Acc: (?P<train_acc>\d+\.\d+)\s+\|\s+"
    r"Val Loss: (?P<val_loss>\d+\.\d+)\s+\|\s+"
    r"Val Acc: (?P<val_acc>\d+\.\d+)\s+\|\s+F1: (?P<val_f1>\d+\.\d+)"
)


def read_notebook_text(path: Path) -> str:
    if not path.exists():
        return ""

    notebook = json.loads(path.read_text(encoding="utf-8"))
    chunks: list[str] = []
    for cell in notebook.get("cells", []):
        chunks.extend(cell.get("source", []))
        for output in cell.get("outputs", []):
            chunks.extend(output.get("text", []))
            data = output.get("data", {})
            chunks.extend(data.get("text/plain", []))
    return "".join(chunks)


def extract_training_log(model_name: str, path: Path) -> pd.DataFrame:
    text = read_notebook_text(path)
    rows = []
    for match in LOG_PATTERN.finditer(text):
        row = match.groupdict()
        rows.append(
            {
                "model": model_name,
                "phase": row["phase"],
                "epoch": int(row["epoch"]),
                "train_loss": float(row["train_loss"]),
                "train_acc": float(row["train_acc"]),
                "val_loss": float(row["val_loss"]),
                "val_acc": float(row["val_acc"]),
                "val_f1": float(row["val_f1"]),
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["step"] = range(1, len(df) + 1)
    return df


def make_clean_phase_ab_log(logs: pd.DataFrame) -> pd.DataFrame:
    """Build the main V4 curve used in the report.

    The notebook contains a resumed Phase A run, so some Phase A epochs appear
    twice in the saved cell output. For report curves, keep the first complete
    Phase A trajectory and append Phase B fine-tuning.
    """
    df = logs[
        (logs["model"] == "VGG16+Inception+ViT_v4")
        & (logs["phase"].isin(["Phase A", "Phase B"]))
    ].copy()

    if df.empty:
        return df

    df = df.sort_values("step")
    df = df.drop_duplicates(subset=["phase", "epoch"], keep="first")
    df["plot_epoch"] = range(1, len(df) + 1)
    return df


def make_staged_log(logs: pd.DataFrame) -> pd.DataFrame:
    df = logs[
        (logs["model"] == "VGG16+Inception+ViT_v4")
        & (logs["phase"].str.startswith("S"))
    ].copy()

    if df.empty:
        return df

    df = df.sort_values("step")
    df["plot_epoch"] = range(1, len(df) + 1)
    return df


def save_metric_tables() -> pd.DataFrame:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    metrics = pd.DataFrame([BASELINE_TEST, FINAL_TEST])
    metrics.to_csv(OUT_DIR / "test_metric_comparison.csv", index=False)
    FINAL_CLASS_REPORT.to_csv(OUT_DIR / "classification_report_v4.csv", index=False)
    FINAL_CONFUSION_MATRIX.to_csv(OUT_DIR / "confusion_matrix_v4.csv")
    return metrics


def add_phase_boundaries(axes: list[plt.Axes], df: pd.DataFrame) -> None:
    phase_spans = (
        df.groupby("phase", sort=False)["plot_epoch"]
        .agg(["min", "max"])
        .reset_index()
    )

    for _, row in phase_spans.iterrows():
        start = float(row["min"])
        end = float(row["max"])
        label_x = (start + end) / 2

        for ax in axes:
            ax.axvspan(start - 0.5, end + 0.5, alpha=0.05, color="#4C78A8")
            if end < df["plot_epoch"].max():
                ax.axvline(end + 0.5, linestyle="--", linewidth=1, color="#B0B0B0")

        axes[0].text(
            label_x,
            1.02,
            row["phase"],
            transform=axes[0].get_xaxis_transform(),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#333333",
        )


def plot_curve_set(df: pd.DataFrame, filename: str, title_suffix: str) -> None:
    if df.empty:
        print(f"No data found for {filename}; skipped.")
        return

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    axes_list = list(axes)
    add_phase_boundaries(axes_list, df)

    axes[0].plot(df["plot_epoch"], df["train_loss"], marker="o", markersize=3, label="Train loss", linewidth=2)
    axes[0].plot(df["plot_epoch"], df["val_loss"], marker="o", markersize=3, label="Validation loss", linewidth=2)
    axes[0].set_title("Loss")
    axes[0].set_ylabel("Loss")
    axes[0].grid(alpha=0.25)
    axes[0].legend(loc="upper right")

    axes[1].plot(df["plot_epoch"], df["train_acc"], marker="o", markersize=3, label="Train accuracy", linewidth=2)
    axes[1].plot(df["plot_epoch"], df["val_acc"], marker="o", markersize=3, label="Validation accuracy", linewidth=2)
    axes[1].set_title("Accuracy")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_ylim(0, 1.02)
    axes[1].grid(alpha=0.25)
    axes[1].legend(loc="lower right")

    axes[2].plot(
        df["plot_epoch"],
        df["val_f1"],
        marker="o",
        markersize=3,
        label="Validation macro-F1",
        linewidth=2,
        color="#2CA02C",
    )
    best_idx = df["val_f1"].idxmax()
    best_row = df.loc[best_idx]
    axes[2].scatter([best_row["plot_epoch"]], [best_row["val_f1"]], s=70, color="#D62728", zorder=5)
    axes[2].annotate(
        f"Best F1 = {best_row['val_f1']:.3f}",
        xy=(best_row["plot_epoch"], best_row["val_f1"]),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=9,
        color="#D62728",
    )
    axes[2].set_title("Validation macro-F1")
    axes[2].set_xlabel("Epoch ghi log")
    axes[2].set_ylabel("Macro-F1")
    axes[2].set_ylim(0, 1.02)
    axes[2].grid(alpha=0.25)
    axes[2].legend(loc="lower right")

    fig.suptitle(
        f"Đường cong loss, accuracy và macro-F1 - VGG16+Inception+ViT_v4 ({title_suffix})",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(OUT_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_training_curves(logs: pd.DataFrame) -> None:
    if logs.empty:
        print("No training logs found in notebooks; skipped training curve plot.")
        return

    logs.to_csv(OUT_DIR / "training_logs_extracted.csv", index=False)

    phase_ab = make_clean_phase_ab_log(logs)
    staged = make_staged_log(logs)

    phase_ab.to_csv(OUT_DIR / "training_logs_v4_phase_ab_clean.csv", index=False)
    staged.to_csv(OUT_DIR / "training_logs_v4_staged.csv", index=False)

    plot_curve_set(
        phase_ab,
        "training_curves_classifier_v4_phase_ab.png",
        "Phase A/B clean",
    )
    plot_curve_set(
        staged,
        "training_curves_classifier_v4_staged.png",
        "staged unfreezing",
    )

    # Backward-compatible filename used in earlier report drafts.
    plot_curve_set(
        phase_ab,
        "training_curves_VGG16_Inception_ViT_v4.png",
        "Phase A/B clean",
    )


def plot_test_metric_change(metrics: pd.DataFrame) -> None:
    plot_df = metrics.set_index("model")[["loss", "accuracy", "macro_f1"]].T
    ax = plot_df.plot(kind="bar", figsize=(10, 5), width=0.78)
    plt.title("Test metrics before and after F1-oriented improvement")
    plt.xlabel("Metric")
    plt.ylabel("Value")
    plt.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=0)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", fontsize=8, padding=2)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "test_metric_change.png", dpi=220)
    plt.close()


def plot_class_metrics() -> None:
    per_class = FINAL_CLASS_REPORT[FINAL_CLASS_REPORT["class"].isin(CLASS_NAMES)]
    plot_df = per_class.set_index("class")[["precision", "recall", "f1_score"]]
    plot_df.plot(kind="bar", figsize=(11, 5.5), width=0.82)
    plt.title("Precision, recall and F1-score by class - VGG16+Inception+ViT_v4")
    plt.xlabel("Class")
    plt.ylabel("Score")
    plt.ylim(0, 1.05)
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "classification_report_v4_bar.png", dpi=220)
    plt.close()


def plot_confusion_matrix() -> None:
    fig, ax = plt.subplots(figsize=(9, 7))
    image = ax.imshow(FINAL_CONFUSION_MATRIX.values, cmap="Blues")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(CLASS_NAMES)))
    ax.set_yticks(range(len(CLASS_NAMES)))
    ax.set_xticklabels(CLASS_NAMES)
    ax.set_yticklabels(CLASS_NAMES)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    max_value = FINAL_CONFUSION_MATRIX.values.max()
    for row in range(len(CLASS_NAMES)):
        for col in range(len(CLASS_NAMES)):
            value = FINAL_CONFUSION_MATRIX.iloc[row, col]
            color = "white" if value > max_value * 0.55 else "black"
            ax.text(col, row, str(value), ha="center", va="center", color=color, fontsize=9)

    plt.title("Confusion matrix - VGG16+Inception+ViT_v4")
    plt.xlabel("Predicted label")
    plt.ylabel("True label")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "confusion_matrix_v4.png", dpi=220)
    plt.close()


def main() -> None:
    metrics = save_metric_tables()

    all_logs = [
        extract_training_log(model_name, path)
        for model_name, path in NOTEBOOKS.items()
    ]
    
    # Filter out empty dataframes before concatenating to avoid ValueError
    non_empty_logs = [df for df in all_logs if not df.empty]
    if non_empty_logs: # Only concatenate if there are actual logs
        logs = pd.concat(non_empty_logs, ignore_index=True)
    else:
        print("No training logs found in any notebook. Skipping training curve plots.")
        logs = pd.DataFrame() # Provide an empty DataFrame to plot_training_curves

    plot_training_curves(logs)
    plot_test_metric_change(metrics)
    plot_class_metrics()
    plot_confusion_matrix()

    print(f"Exported classifier figures and tables to: {OUT_DIR}")


if __name__ == "__main__":
    main()
