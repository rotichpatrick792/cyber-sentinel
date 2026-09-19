export type Health = {
    status: string;
    environment: string;
    model_loaded: boolean;
    model_error: string | null;
};

export type PredictResponse = {
    label: string;
    confidence: number;
    probabilities: Record<string, number>;
};
