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
export type FlowRecord = {
    src_ip: string;
    src_port: number;
    dst_ip: string;
    dst_port: number;
    protocol: number;
    label: string;
    confidence: number;
    timestamp: string | null;
};

export type FlowsRecentResponse = {
    flows: FlowRecord[];
    total: number;
};
