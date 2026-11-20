# Data and resource provenance — 2.0

## Original trained model

The supplied `tomato_best.pt` is preserved unchanged. The earlier project identifies `Project-AgML/tomato_leaf_disease` as the source for its selected five tomato classes. The original training dataset and full experiment were not rerun here; earlier same-source test percentages are not independently verified field performance. Hash and taxonomy are in MODEL_CARD.md.

## Added detection weights

- Publisher: NarimanOsman2025, Hugging Face `tomato-disease-detector-yolov8n`.
- Pinned revision: `1e57e122a6aaa2aba5532e72b10f5cc78b49219d`.
- Weight URL: `https://huggingface.co/NarimanOsman2025/tomato-disease-detector-yolov8n/resolve/1e57e122a6aaa2aba5532e72b10f5cc78b49219d/best.pt`.
- Upstream declares CC BY 4.0; attribution and the unchanged upstream model card are included. Model metadata and actual taxonomy were inspected, and the downloaded hash was verified.
- The publisher reports 2,977 combined images, split into 2,226 training / 449 validation / 302 test, using Roboflow datasets identified in the included card. Its reported overall mAP50 is about 0.686; per-class performance varies substantially. We did not download or independently audit that whole dataset or verify its split/leakage.
- Model weights are included, not a newly trained model or a complete redistribution of the training datasets. No new crop capability or magnesium class has been added by changing labels.

## User-supplied references reviewed

| Reference | Finding and use |
| --- | --- |
| jethromoleno/tomato-leaf-disease-detection-yolo | YOLOv5 training/data workflow and six-class project; reference, not a verified drop-in model for this app |
| RKIzmailov/tomato-leaf-diseases-detection | Seven-class detector. Candidate weight tested on the K-State example; it predicted Late Blight. Not bundled as a replacement |
| ujjwal540/Tomato-Disease-Detection-YOLOv8 | Seven-class detector. Candidate predicted Early Blight on that one example; one success is not comparative accuracy. No clear redistribution license found in inspected root; not bundled |
| harisushehu/YOLO-for-detection-of-tomato-leaf-diseases | TomatoEbola/Tuta absoluta damage research. Not evidence that an installed model recognizes every tomato disease |
| Aditya07-SD/Tomato-Plant-Disease-Detection-using-YOLOv8 | README says trained weights are not included. Architecture/reference only |
| Sanila-577/yolo-tomato-disease-detector | Seven-class vision + cloud/RAG project; weight entry is a Git LFS pointer, not a complete embedded checkpoint. Cloud RAG is not an offline disease engine |
| Zenodo 20777853 / supplied YOLOv11 + DeiTBlock ZIP | Source scripts only, no usable trained checkpoint or dataset in the supplied archive. Custom code was inspected, not executed as a pretrained replacement |
| `202411411981210(1).pdf` | Bellout et al., Advanced YOLO models for real-time detection of tomato leaf diseases, Mathematical Modeling and Computing 11(4), 2024. Research reference, not our validation result |
| scanned `Screenshot 2026-11-14 023027(1).pdf` | Screenshots of a YOLO tomato preprint and its methodology/results. It explicitly labels itself not peer reviewed; no runnable trained model was obtained from it |

URLs are the public user-supplied GitHub repository paths. Reference screenshots showing disease labels illustrate the requested visual treatment; their bounding boxes and accuracy claims were not copied as model output.

## Offline knowledge sources

Curated bilingual paraphrases live in `backend/knowledge.py` and are exported in `data/knowledge/tomato_guides.json` for review. There are 26 guide entries, including diseases, pests, physiological disorders, Healthy interpretation and watering. Each has cause, symptoms, care, prevention and source metadata. This is a finite expert-source guide library, not an autonomous offline language model.

Bundled sources: K-State L721 (May 2009) and Iowa State PM1266 (August 2006). Page numbers refer to these exact supplied PDFs. Iowa's current catalog links to a revised PD54 edition; the edition difference is disclosed. Other sources include UC IPM for yellow curl, mosaic and leafminers; UConn for mites; UF IFAS for target spot; SDSU Extension for magnesium deficiency. No pesticide or fertilizer dose is generated. Country-specific pesticide authorization is not inferred from US extension publications.

Source URLs are retained per entry. Content was paraphrased and translated; it is not a claim of formal Bangla agronomic validation. No new image training is created by writing these guides.

## QA assets

`tests/assets/QA_TEST_KSTATE_EARLY_BLIGHT_NOT_LIVE.jpg`: K-State L721 figure 2, labeled Early Blight, used for a model integration smoke test. It is not a live camera frame or a withheld field benchmark.

`QA_SCREENSHOT_DERIVED_*_UNKNOWN_DIAGNOSIS.jpg`: cropped from the user's 021047, 021149 and 021234 screenshots solely as small pipeline test inputs. Their true diagnoses are unknown. Their inferenced labels are not ground truth. Resulting annotations are explicitly QA artifacts under docs.

## Optional future training

The existing duplicate-aware ten-class preparation and training pipeline is retained. The dataset is not packaged. Review its license and create an independent, annotated validation set representative of the user's real camera, cultivar and lighting before making accuracy claims. Only models with a verified task/taxonomy are selectable. Magnesium and non-tomato crops need separate appropriately labeled data and trained/validated weights.
