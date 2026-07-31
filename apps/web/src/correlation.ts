export interface CorrelationPoint {
  x: number;
  y: number;
}

export type PearsonCorrelationResult =
  | {
      status: "defined";
      pair_count: number;
      coefficient: number;
    }
  | {
      status: "insufficient_pairs";
      pair_count: number;
      coefficient: null;
    }
  | {
      status: "zero_variance";
      pair_count: number;
      coefficient: null;
      constant_axes: readonly ("x" | "y")[];
    };

export function pearsonCorrelation(
  points: readonly CorrelationPoint[],
): PearsonCorrelationResult {
  if (points.length < 2) {
    validateFinitePoints(points);
    return {
      status: "insufficient_pairs",
      pair_count: points.length,
      coefficient: null,
    };
  }

  let meanX = 0;
  let meanY = 0;
  points.forEach((point, index) => {
    validateFinitePoint(point);
    const count = index + 1;
    meanX += (point.x - meanX) / count;
    meanY += (point.y - meanY) / count;
  });
  if (!Number.isFinite(meanX) || !Number.isFinite(meanY)) {
    throw new Error("correlation mean is not finite");
  }

  let maximumDeviationX = 0;
  let maximumDeviationY = 0;
  for (const point of points) {
    maximumDeviationX = Math.max(maximumDeviationX, Math.abs(point.x - meanX));
    maximumDeviationY = Math.max(maximumDeviationY, Math.abs(point.y - meanY));
  }

  const constantAxes: ("x" | "y")[] = [];
  if (maximumDeviationX === 0) constantAxes.push("x");
  if (maximumDeviationY === 0) constantAxes.push("y");
  if (constantAxes.length > 0) {
    return {
      status: "zero_variance",
      pair_count: points.length,
      coefficient: null,
      constant_axes: constantAxes,
    };
  }

  const products: number[] = [];
  const squaresX: number[] = [];
  const squaresY: number[] = [];
  for (const point of points) {
    const normalizedX = (point.x - meanX) / maximumDeviationX;
    const normalizedY = (point.y - meanY) / maximumDeviationY;
    products.push(normalizedX * normalizedY);
    squaresX.push(normalizedX * normalizedX);
    squaresY.push(normalizedY * normalizedY);
  }

  const covariance = compensatedSum(products);
  const varianceX = compensatedSum(squaresX);
  const varianceY = compensatedSum(squaresY);
  const denominator = Math.sqrt(varianceX * varianceY);
  const rawCoefficient = covariance / denominator;
  if (!Number.isFinite(rawCoefficient)) {
    throw new Error("correlation coefficient is not finite");
  }

  return {
    status: "defined",
    pair_count: points.length,
    coefficient: Math.max(-1, Math.min(1, rawCoefficient)),
  };
}

export function correlationSummaryHtml(
  points: readonly CorrelationPoint[],
  xLabel: string,
  yLabel: string,
): string {
  const result = pearsonCorrelation(points);
  if (result.status === "insufficient_pairs") {
    return `
      <section class="scatter-card correlation-card" aria-labelledby="correlation-heading">
        <p class="eyebrow">Linear association</p>
        <h3 id="correlation-heading">Pearson correlation is undefined</h3>
        <p>At least two complete pairs are required; ${result.pair_count} ${result.pair_count === 1 ? "is" : "are"} available.</p>
        <p class="chart-note">Missing values are excluded, never converted to zero. Correlation does not imply causation.</p>
      </section>`;
  }

  if (result.status === "zero_variance") {
    const labels = result.constant_axes.map((axis) => axis === "x" ? xLabel : yLabel);
    return `
      <section class="scatter-card correlation-card" aria-labelledby="correlation-heading">
        <p class="eyebrow">Linear association</p>
        <h3 id="correlation-heading">Pearson correlation is undefined</h3>
        <p>${escapeHtml(joinLabels(labels))} ${labels.length === 1 ? "has" : "have"} no variation across the ${result.pair_count} complete pairs.</p>
        <p class="chart-note">A correlation coefficient requires variation on both axes. Correlation does not imply causation.</p>
      </section>`;
  }

  const coefficient = displayCoefficient(result.coefficient);
  const direction = result.coefficient > 0
    ? "positive"
    : result.coefficient < 0
      ? "negative"
      : "zero";
  return `
    <section class="scatter-card correlation-card" aria-labelledby="correlation-heading">
      <div class="chart-heading">
        <div>
          <p class="eyebrow">Linear association</p>
          <h3 id="correlation-heading">Pearson correlation</h3>
        </div>
        <strong aria-label="Pearson correlation coefficient ${escapeHtml(coefficient)}">r = ${escapeHtml(coefficient)}</strong>
      </div>
      <div class="coverage-metrics">
        <div><span>Complete pairs</span><strong>${result.pair_count}</strong></div>
        <div><span>Direction</span><strong>${direction}</strong></div>
        <div><span>Method</span><strong>Pearson r</strong></div>
      </div>
      <p>${escapeHtml(yLabel)} and ${escapeHtml(xLabel)} have a ${direction} linear association in the selected complete pairs.</p>
      <p class="chart-note">This is descriptive association only. Missing values are excluded, and correlation does not imply causation.</p>
    </section>`;
}

function validateFinitePoints(points: readonly CorrelationPoint[]): void {
  for (const point of points) validateFinitePoint(point);
}

function validateFinitePoint(point: CorrelationPoint): void {
  if (!Number.isFinite(point.x) || !Number.isFinite(point.y)) {
    throw new Error("correlation points must contain finite x and y values");
  }
}

function compensatedSum(values: readonly number[]): number {
  let sum = 0;
  let correction = 0;
  for (const value of values) {
    const next = sum + value;
    correction += Math.abs(sum) >= Math.abs(value)
      ? (sum - next) + value
      : (value - next) + sum;
    sum = next;
  }
  return sum + correction;
}

function displayCoefficient(value: number): string {
  const normalized = Object.is(value, -0) ? 0 : value;
  return normalized.toFixed(3);
}

function joinLabels(labels: readonly string[]): string {
  if (labels.length === 1) return labels[0] ?? "The selected feature";
  return `${labels[0] ?? "The x feature"} and ${labels[1] ?? "the y feature"}`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      '"': "&quot;",
    };
    return entities[character] ?? character;
  });
}
