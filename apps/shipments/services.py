class AIRiskService:
    @staticmethod
    def analyze_verification_images(images, declared_weight=None, declared_dimensions=None):
        """
        Mocks the AI Risk Engine.
        In production, this would call an external ML model or service to analyze:
        - Image similarity/quality
        - Duplicate detection
        - Weight mismatch
        - Dimension mismatch
        """
        # Very basic mock: if more than 5 images, flag as risk (just as a mock rule)
        if len(images) > 5:
            return {
                "status": "High Risk",
                "score": 85,
                "flags": ["Too many images indicating potential tampering"]
            }
        
        # If any condition notes contain 'broken', flag as risk
        return {
            "status": "Low Risk",
            "score": 15,
            "flags": []
        }
