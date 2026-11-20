# Model card — AgriVision 2.0

## Files preserved and added

| File | Role | SHA-256 |
| --- | --- | --- |
| `models/tomato_best.pt` | User-trained YOLO26n whole-image classifier; preserved byte-for-byte, 3,194,562 bytes | `d3e816f6d02cd74f3d4b0fd6d756b8bcd93a7efefd9c41920f30a02af3bf3007` |
| `models/tomato_detector_9class.pt` | Pretrained secondary YOLOv8n detector, downloaded from the pinned upstream revision; not trained in this work | `ccc05ab88bb550567fb7a7a07c564d37e344e7e69e094da54481ea47c0f134b3` |

The original classes are Bacterial Spot, Early Blight, Healthy, Late Blight and Yellow Leaf Curl Virus. The secondary model has Early Blight, Septoria Leaf Spot, Healthy, Bacterial Spot, Late Blight, Tomato Mosaic Virus, Tomato Yellow Virus, Leaf Mold and Spider Mites. Its generic yellow-virus class must not be equated with laboratory identification of TYLCV.

## Runtime profiles

`hybrid`, the default, uses the secondary detector's actual coordinates and the preserved five-class classifier for each proposed region. A proposal covering at least 80% of the image uses the full image for classification, avoiding an additional disruptive crop. Smaller proposals are classified individually. The detector label, localization score, classifier alternatives, classification input and disagreements are retained. Different predictions trigger REVIEW; low classifier score or margin yields an uncertain condition rather than a disease label. Geometry is not invented from classifier output.

`detector9` exposes the secondary model's own nine labels. It is an optional wider-coverage profile with unverified field reliability. `original` exposes the preserved classifier, with no fake bounding boxes. `expanded` is available only if separately trained ten-class classification weights are installed.

Detection uses image size 640, minimum score 0.40, NMS IoU 0.5, class-agnostic suppression and at most 8 regions. Classification uses image size 224, score at least 0.75 and top-two margin at least 0.15. These are engineering thresholds, not calibration or clinical/agronomic operating guarantees. Three consistent live predictions reduce display flicker; every fresh bad/no-detection frame immediately clears previous results. Saved captures are single-image observations.

## Evidence and limitations

- Real CPU smoke: the labeled K-State L721 figure 2 Early Blight image receives Early Blight ≈0.954 from the preserved classifier. The secondary detector incorrectly labels its region Tomato Yellow Virus ≈0.911. The default profile exposes this as REVIEW, with both labels available. This is a known model error, not a solved accuracy problem.
- Three screenshot-derived user inputs were tested without disease ground truth. Two returned NO_DETECTION; the third produced several proposed leaf regions. See `docs/qa-model-smoke.json`. These inputs are small compressed screenshots, not full-resolution original photos and not a field validation set.
- No new accuracy, precision, recall, field mAP, disease severity or calibrated probability was measured. The upstream model card's metrics are publisher reports, not this release's validation.
- Blank, dark, heavily overexposed, uniform and very blurred inputs are screened using simple image-quality heuristics. The heuristics are not a trained leaf detector. The detector is also not a validated universal leaf/crop/OOD verifier.
- Boxes indicate predicted leaf/condition regions. They are not pixel-level lesions or lesion severity. Healthy and no-detection are different states; no box does not imply a healthy plant.
- No installed visual class covers magnesium deficiency, leafminer, all tomato conditions or non-tomato crops. Offline knowledge about an untrained problem does not add visual support.
- A five-class classifier can force an unsupported condition into its available classes. A high score cannot remove that risk. Direct nine-label mode can also be wrong.
- Wide aerial footage, overlapping tiny leaves, phone-screen glare, cultivar/background changes and field lighting are outside demonstrated accuracy. A close single leaf is the appropriate demonstration input.

## Provenance and licensing

Secondary weights: [NarimanOsman2025/tomato-disease-detector-yolov8n](https://huggingface.co/NarimanOsman2025/tomato-disease-detector-yolov8n), revision `1e57e122a6aaa2aba5532e72b10f5cc78b49219d`. Upstream declares CC BY 4.0. Attribution, dataset links and original card are retained in `models/detector_provenance.json` and `references/DETECTOR_MODEL_CARD_UPSTREAM.md`. Weights were integrated unchanged. Ultralytics software has its own AGPL-3.0/enterprise licensing; the model card's weight license does not replace dependency terms.

No training was run. Optional ten-class preparation/training scripts preserve the original file and write a separately named model and evaluation report. A ten-class classifier still does not generate boxes. Independent, annotated local validation is needed before describing this as a reliable field disease diagnostic system.
