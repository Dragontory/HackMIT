from typing import List, Tuple


class ClipScorer:
    """
    Safe CLIP wrapper. If open_clip is unavailable, returns neutral scores.
    score_pairs takes a list of (image_path, text) and returns a list[float].
    """

    def __init__(self, model_name: str, pretrained: str):
        self._ok = False
        try:
            import torch  # noqa
            import open_clip  # noqa
            self._ok = True
            self._load(model_name, pretrained)
        except Exception:
            # No CLIP available; stay in fallback mode.
            self._ok = False

    def _load(self, model_name: str, pretrained: str):
        import torch
        import open_clip
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained
        )
        self.tokenizer = open_clip.get_tokenizer(model_name)
        self.model.to(self.device).eval()

    def score_pairs(self, pairs: List[Tuple[str, str]]) -> List[float]:
        if not self._ok:
            # Fallback: neutral scores so threshold may filter few/none
            return [0.5 for _ in pairs]
        import torch
        from PIL import Image
        import open_clip

        scores: List[float] = []
        with torch.no_grad():
            for img_path, text in pairs:
                try:
                    image = self.preprocess(Image.open(img_path).convert(
                        "RGB")).unsqueeze(0).to(self.device)
                    text_tokens = self.tokenizer([text]).to(self.device)
                    img_feat = self.model.encode_image(image)
                    txt_feat = self.model.encode_text(text_tokens)
                    img_feat /= img_feat.norm(dim=-1, keepdim=True)
                    txt_feat /= txt_feat.norm(dim=-1, keepdim=True)
                    sim = (img_feat @ txt_feat.T).squeeze().item()
                    # map cosine [-1,1] -> [0,1]
                    scores.append(0.5 * (sim + 1.0))
                except Exception:
                    scores.append(0.0)
        return scores
