import {
  parseExplorationRecipeV1,
  type ExplorationRecipeV1,
  type Operation,
  type Visualization,
} from "../../../packages/contracts/src/index.js";
import type { ExplorerScope } from "./explorer.js";

const MAX_TOKEN_CHARACTERS = 32_768;
const MAX_DECOMPRESSED_BYTES = 65_536;

export class RecipeUrlError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RecipeUrlError";
  }
}

export function recipeForSelection(
  releaseId: string,
  operation: Operation,
  indicatorVariantIds: readonly string[],
  scope: ExplorerScope,
): ExplorationRecipeV1 {
  const geographyIds = scope.geography_ids ? [...scope.geography_ids].sort((a, b) => a - b) : [];
  const periods = scope.periods ? [...scope.periods].sort() : [];
  return parseExplorationRecipeV1({
    schema_version: 1,
    release_id: releaseId,
    operation,
    indicator_variant_ids: [...indicatorVariantIds],
    visualization: visualizationForOperation(operation),
    geography: {
      mode: geographyIds.length > 0 ? "include" : "all_compatible",
      geography_ids: geographyIds,
    },
    time: {
      mode: periods.length > 0 ? "include" : "all_compatible",
      periods,
    },
    transforms: [],
  });
}

export function visualizationForOperation(operation: Operation): Visualization {
  switch (operation) {
    case "map": return "map";
    case "trend": return "line";
    case "table": return "table";
    case "scatter":
    case "correlation": return "scatter";
    case "ratio": return "line";
  }
}

export async function encodeRecipeToken(recipe: ExplorationRecipeV1): Promise<string> {
  const validated = parseExplorationRecipeV1(recipe);
  const raw = new TextEncoder().encode(JSON.stringify(canonicalize(validated)));
  const compressed = await transform(raw, new CompressionStream("deflate"), MAX_DECOMPRESSED_BYTES);
  return bytesToBase64Url(compressed);
}

export async function decodeRecipeToken(token: string): Promise<ExplorationRecipeV1> {
  if (!token || token.length > MAX_TOKEN_CHARACTERS) {
    throw new RecipeUrlError("recipe token is empty or too large");
  }
  try {
    const compressed = base64UrlToBytes(token);
    const raw = await transform(
      compressed,
      new DecompressionStream("deflate"),
      MAX_DECOMPRESSED_BYTES,
    );
    return parseExplorationRecipeV1(JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(raw)));
  } catch (error) {
    if (error instanceof RecipeUrlError) throw error;
    throw new RecipeUrlError("invalid recipe token");
  }
}

export async function recipeFromUrl(url: string): Promise<ExplorationRecipeV1 | null> {
  const values = new URL(url).searchParams.getAll("r");
  if (values.length === 0) return null;
  if (values.length !== 1) throw new RecipeUrlError("URL must contain exactly one recipe parameter");
  const token = values[0];
  if (!token) throw new RecipeUrlError("recipe parameter cannot be empty");
  return decodeRecipeToken(token);
}

export async function urlWithRecipe(url: string, recipe: ExplorationRecipeV1): Promise<string> {
  const parsed = new URL(url);
  parsed.searchParams.delete("r");
  parsed.searchParams.set("r", await encodeRecipeToken(recipe));
  return parsed.toString();
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (typeof value === "object" && value !== null) {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, item]) => [key, canonicalize(item)]),
    );
  }
  return value;
}

async function transform(
  input: Uint8Array,
  stream: CompressionStream | DecompressionStream,
  maximumBytes: number,
): Promise<Uint8Array> {
  const reader = stream.readable.getReader();
  const writer = stream.writable.getWriter();
  const readPromise = collectTransformedBytes(reader, maximumBytes);
  const writePromise = (async (): Promise<void> => {
    await writer.write(input);
    await writer.close();
  })();

  try {
    const [output] = await Promise.all([readPromise, writePromise]);
    return output;
  } catch (error) {
    await Promise.allSettled([writer.abort(error), reader.cancel(error)]);
    throw error;
  }
}

async function collectTransformedBytes(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  maximumBytes: number,
): Promise<Uint8Array> {
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maximumBytes) {
      throw new RecipeUrlError("decoded recipe is too large");
    }
    chunks.push(value);
  }
  const output = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return output;
}

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlToBytes(token: string): Uint8Array {
  if (!/^[A-Za-z0-9_-]+$/.test(token)) throw new RecipeUrlError("invalid recipe token");
  const base64 = token.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - token.length % 4) % 4);
  const binary = atob(base64);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}
