export interface DimensionDetail {
    dimension: string;
    score: number;
    details: string;
    recommendations: string[];
}

export interface AssessmentResult {
    timestamp: string;
    domain: string | null;
    overall_score: number;
    dimensions: Record<string, number>;
    dimension_details: DimensionDetail[];
    recommendations: string[];
    metadata: Record<string, any>;
}

export interface FeedbackStats {
    overall: {
        total_feedback: number;
        avg_rating: number;
        useful_rate: number;
        correction_rate: number;
    };
    by_agent: Record<string, any>;
    low_rated_requests: any[];
}

export interface RegisteredAgent {
    agent_id: string;
    name: string;
    domains: string[];
    registered_at: string;
    last_active: string | null;
}

export interface KnowledgeExchange {
    request_id: string;
    sender_agent_id: string;
    domain: string;
    query: string;
    confidence: number;
    timestamp: string;
}
