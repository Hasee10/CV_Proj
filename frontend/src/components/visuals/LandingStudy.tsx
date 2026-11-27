import { Link } from "react-router-dom";
import type { CaptureState } from "../../hooks/useSavedCapture";
import type { BenchmarkResult, FieldResult } from "../../api/results";

export function WorkflowSection({ capture }: { capture: CaptureState }) {
  const record = capture.manifest?.records.find(
    (r) => r.id === "numeric-proposed",
  );
  const result = capture.responses["numeric-proposed"] as
    | FieldResult
    | undefined;
  return (
    <section
      className="landing-workflow"
      id="workflow"
      aria-labelledby="workflow-title"
    >
      <div className="section-heading">
        <p className="section-label">THE WORKFLOW</p>
        <h2 id="workflow-title">
          From a handwritten field
          <br />
          to a traceable result.
        </h2>
        <p>
          Read the original image, inspect the recognised text, and see how the
          value was interpreted. Every step stays visible.
        </p>
      </div>
      <div className="workflow-layout">
        <ol className="workflow-steps">
          <li>
            <span>01</span>
            <div>
              <h3>Start with the evidence.</h3>
              <p>
                The original field crop remains beside its result. Our current
                workspace uses clearly labelled development examples.
              </p>
            </div>
          </li>
          <li>
            <span>02</span>
            <div>
              <h3>Read what the model read.</h3>
              <p>
                LoGo-HTR returns the raw text. ATHN prepares text at a suitable
                scale before the same recogniser.
              </p>
            </div>
          </li>
          <li>
            <span>03</span>
            <div>
              <h3>Make the comparison visible.</h3>
              <p>
                Parsed numeric and written amounts either agree, differ, or
                require human review when a value cannot be read.
              </p>
            </div>
          </li>
        </ol>
        <figure className="landing-specimen">
          <figcaption>
            <span>AN ACTUAL MODEL RESPONSE</span>
            <span>ATHN / DEV</span>
          </figcaption>
          {record && result ? (
            <>
              <div className="specimen-image">
                <img
                  src={record.image}
                  alt="Original synthetic numeric development crop"
                />
              </div>
              <div className="specimen-output">
                <span>Raw recognised text</span>
                <strong>{result.raw_text}</strong>
              </div>
              <div className="specimen-parsed">
                <span>Parsed value</span>
                <strong>{result.parsed_value ?? "Not parsed"}</strong>
              </div>
              <p>Synthetic input · recorded response · not an accuracy claim</p>
              <Link to="/recognize">
                Inspect this result <span aria-hidden="true">↗</span>
              </Link>
            </>
          ) : (
            <p role="status">
              {capture.error ?? "Loading the recorded example…"}
            </p>
          )}
        </figure>
      </div>
    </section>
  );
}

export function EvidenceSection({ capture }: { capture: CaptureState }) {
  const benchmark = capture.responses.benchmark as BenchmarkResult | undefined;
  const genuine = benchmark?.datasets.D1_gnhk_words_genuine;
  const synthetic = benchmark?.datasets.D6_syn_numeric_SYNTHETIC;
  return (
    <section
      className="landing-evidence"
      id="evidence"
      aria-labelledby="evidence-title"
    >
      <div className="section-heading">
        <p className="section-label">THE RESEARCH, IN CONTEXT</p>
        <h2 id="evidence-title">
          Show the gains.
          <br />
          Keep the limits in view.
        </h2>
        <p>
          Baseline and ATHN use the same frozen model. Genuine handwriting and
          synthetic fields are evaluated separately.
        </p>
      </div>
      {genuine && synthetic ? (
        <div className="evidence-comparison">
          <article>
            <span className="evidence-category">
              GENUINE HANDWRITING · {genuine.n_eligible} WORD CROPS
            </span>
            <h3>Character error rate</h3>
            <div className="evidence-numbers">
              <div>
                <span>Baseline</span>
                <strong>{genuine.cer.baseline}</strong>
              </div>
              <span aria-hidden="true">→</span>
              <div>
                <span>ATHN</span>
                <strong>{genuine.cer.proposed}</strong>
              </div>
            </div>
            <p>
              One genuine subset. The overall genuine-handwriting change was not
              statistically significant.
            </p>
          </article>
          <article>
            <span className="evidence-category">
              SYNTHETIC NUMBERS · {synthetic.n_eligible} CROPS
            </span>
            <h3>Exact parsed values</h3>
            <div className="evidence-numbers">
              <div>
                <span>Baseline</span>
                <strong>
                  {synthetic.value_exact?.baseline}
                  <small> / {synthetic.value_exact?.n}</small>
                </strong>
              </div>
              <span aria-hidden="true">→</span>
              <div>
                <span>ATHN</span>
                <strong>
                  {synthetic.value_exact?.proposed}
                  <small> / {synthetic.value_exact?.n}</small>
                </strong>
              </div>
            </div>
            <p>
              Font-rendered fields. These results do not establish performance
              on real handwritten cheques.
            </p>
          </article>
        </div>
      ) : (
        <p role="status">{capture.error ?? "Loading the saved research…"}</p>
      )}
      <div className="evidence-footnote">
        <p>
          Existing locked-test results. No evaluation runs when you open this
          page.
        </p>
        <Link to="/benchmarks">
          Explore the full evidence <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </section>
  );
}
