export type Mode = "baseline" | "proposed";
export interface Health {
  status: "ok" | "model_unavailable";
  model_loaded: boolean;
}
export interface MethodConfig {
  id: string;
  method: string;
  band_lo: number;
  band_hi: number;
  target: number;
  min_scale: number;
  max_scale: number;
}
export interface ModelInfo {
  model: string;
  checkpoint_sha256: string;
  upstream_commit: string;
  parameter_count: number | null;
  dictionary: string;
  preprocessing: string;
  decoding: string;
  device: string;
  default_mode: Mode;
  ready: boolean;
  modes: {
    baseline: string;
    proposed: {
      method: string;
      config: MethodConfig | null;
      status: string | null;
    };
  };
  limitations: string[];
}
export interface BackendError {
  code: string;
  message: string;
  request_id: string;
}
