// Generated from exact local API response captures. See public/gallery/samples.json.
export const sampleStudies = [
  {
    id: "digits",
    title: "A longer digit string.",
    split: "dev",
    synthetic: false,
    source_path: "data/benchmarks/cvl_numeric/CVL_135579_0002_10.png",
    source_id: "CVL_135579_0002_10",
    licence: "CC-BY-NC-4.0",
    image: "/results/20261128T054632Z-gallery/CVL_135579_0002_10.png",
    image_sha256:
      "40ee5ce4a185d4a56babdbe1dc929de495582a2a7494b6dd1c462c62e5dc455a",
    responses: {
      baseline: {
        path: "/results/20261128T054632Z-gallery/digits-baseline.json",
        sha256:
          "2348696d2e2c7514c705e47b55304d8947983f03991f921d17f14f13ae7f6637",
        request_id: "dd7af7d6a4a7",
        result: {
          field_type: "numeric",
          mode: "baseline",
          raw_text: "135529",
          parsed_value: "135529.00",
          parse_status: "parsed",
          beam_log_probability: -0.295,
          preprocessing: {
            method: "baseline",
            applied: false,
            path: "identity",
          },
          model_input_shape: [1, 3, 77, 271],
          latency_seconds: {
            preprocess: 0.0004,
            queue_wait: 0.0002,
            inference: 2.8702,
            total: 2.8708,
          },
          image: {
            width: 271,
            height: 77,
          },
          request_id: "dd7af7d6a4a7",
        },
      },
      proposed: {
        path: "/results/20261128T054632Z-gallery/digits-proposed.json",
        sha256:
          "d86ec6581d407ac6aa38cd877672fdce60095bb68fee43c7121644651c22d2a5",
        request_id: "b82b0908d4c0",
        result: {
          field_type: "numeric",
          mode: "proposed",
          raw_text: "135529",
          parsed_value: "135529.00",
          parse_status: "parsed",
          beam_log_probability: -0.295,
          preprocessing: {
            method: "ATHN",
            estimated_text_height: 54.800000000000004,
            input_hw: [77, 271],
            scale: 1.0,
            applied: false,
            path: "identity",
          },
          model_input_shape: [1, 3, 77, 271],
          latency_seconds: {
            preprocess: 0.0552,
            queue_wait: 0.0,
            inference: 2.9233,
            total: 2.9785,
          },
          image: {
            width: 271,
            height: 77,
          },
          request_id: "b82b0908d4c0",
        },
      },
    },
  },
  {
    id: "handwriting",
    title: "A small handwritten field.",
    split: "dev",
    synthetic: false,
    source_path: "data/benchmarks/gnhk_pairs/GNHKP_eng_EU_310_w016.png",
    source_id: "GNHKP_eng_EU_310_w016",
    licence: "CC-BY-4.0",
    image: "/results/20261128T054632Z-gallery/GNHKP_eng_EU_310_w016.png",
    image_sha256:
      "5da1b147115ef2167c88fbcf08b5eb98426159f9c7909507baefacd357897328",
    responses: {
      baseline: {
        path: "/results/20261128T054632Z-gallery/handwriting-baseline.json",
        sha256:
          "5b02eef2a368fa12a44b87fe577fb577a1ac899aebe3766d65980e6598af10c6",
        request_id: "8b15b1b627f1",
        result: {
          field_type: "numeric",
          mode: "baseline",
          raw_text: "a",
          parsed_value: null,
          parse_status: "unparseable",
          beam_log_probability: -1.471,
          preprocessing: {
            method: "baseline",
            applied: false,
            path: "identity",
          },
          model_input_shape: [1, 3, 18, 17],
          latency_seconds: {
            preprocess: 0.0,
            queue_wait: 0.0,
            inference: 0.7875,
            total: 0.7875,
          },
          image: {
            width: 17,
            height: 18,
          },
          request_id: "8b15b1b627f1",
        },
      },
      proposed: {
        path: "/results/20261128T054632Z-gallery/handwriting-proposed.json",
        sha256:
          "149cd8b0cf85cd11acf5e85d6f08362b6108fa57eb2d8af62046468dbcbb59bd",
        request_id: "1efb9816d577",
        result: {
          field_type: "numeric",
          mode: "proposed",
          raw_text: "7",
          parsed_value: "7.00",
          parse_status: "parsed",
          beam_log_probability: -0.9815,
          preprocessing: {
            method: "ATHN",
            estimated_text_height: 11.0,
            input_hw: [18, 17],
            scale: 4.0,
            applied: true,
            path: "resized",
            output_hw: [72, 68],
          },
          model_input_shape: [1, 3, 72, 68],
          latency_seconds: {
            preprocess: 0.0023,
            queue_wait: 0.0,
            inference: 1.983,
            total: 1.9853,
          },
          image: {
            width: 17,
            height: 18,
          },
          request_id: "1efb9816d577",
        },
      },
    },
  },
  {
    id: "synthetic",
    title: "Another scale. Another reading.",
    split: "dev",
    synthetic: true,
    source_path: "data/benchmarks/syn_cheques/SYN_0013_num.png",
    source_id: "SYN_0013_num",
    licence:
      "Apache-2.0 (declared on the HF card; underlying template provenance undocumented)",
    image: "/results/20261128T054632Z-gallery/SYN_0013_num.png",
    image_sha256:
      "b0a0340edf7fc39fc025402693b7540ebf3d5195255111ac9074977641f07392",
    responses: {
      baseline: {
        path: "/results/20261128T054632Z-gallery/synthetic-baseline.json",
        sha256:
          "850111315b1a210095874a755ed0cd46fca893d90cfc08c8de5c9de0f7373288",
        request_id: "97747aa7d07f",
        result: {
          field_type: "numeric",
          mode: "baseline",
          raw_text: "ting",
          parsed_value: null,
          parse_status: "unparseable",
          beam_log_probability: -1.7919,
          preprocessing: {
            method: "baseline",
            applied: false,
            path: "identity",
          },
          model_input_shape: [1, 3, 37, 111],
          latency_seconds: {
            preprocess: 0.0,
            queue_wait: 0.0,
            inference: 1.8198,
            total: 1.8198,
          },
          image: {
            width: 111,
            height: 37,
          },
          request_id: "97747aa7d07f",
        },
      },
      proposed: {
        path: "/results/20261128T054632Z-gallery/synthetic-proposed.json",
        sha256:
          "253fd4716fd8cc813106e6b898d3e34130c3b7abb741be978b6767cb7ae3a1c2",
        request_id: "d26210f2db83",
        result: {
          field_type: "numeric",
          mode: "proposed",
          raw_text: "1737",
          parsed_value: "1737.00",
          parse_status: "parsed",
          beam_log_probability: -0.4964,
          preprocessing: {
            method: "ATHN",
            estimated_text_height: 16.0,
            input_hw: [37, 111],
            scale: 3.0,
            applied: true,
            path: "resized",
            output_hw: [111, 333],
          },
          model_input_shape: [1, 3, 111, 333],
          latency_seconds: {
            preprocess: 0.0074,
            queue_wait: 0.0,
            inference: 5.8131,
            total: 5.8205,
          },
          image: {
            width: 111,
            height: 37,
          },
          request_id: "d26210f2db83",
        },
      },
    },
  },
] as const;
