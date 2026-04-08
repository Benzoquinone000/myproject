/**
 * 从 LangChain / MCP 工具返回的 content 中解析可展示的图表或图片 URL。
 * 兼容：纯 URL、Markdown 图片、JSON（含 AntV resultObj）、data: URI。
 */

function normalizeToolResultContent(content) {
  if (content == null) return null;
  if (Array.isArray(content)) {
    const parts = content
      .map((c) => {
        if (typeof c === 'string') return c;
        if (c && typeof c === 'object' && typeof c.text === 'string') return c.text;
        return '';
      })
      .filter(Boolean);
    return parts.join('\n') || null;
  }
  return content;
}

/**
 * @param {unknown} content - tool_call_result.content
 * @returns {string|null} 可用于 <img src> 的地址
 */
export function extractChartImageUrl(content) {
  const raw = normalizeToolResultContent(content);
  if (raw == null || raw === '') return null;

  if (typeof raw === 'object' && raw !== null) {
    return extractFromObject(raw);
  }

  if (typeof raw !== 'string') {
    return null;
  }

  const trimmed = raw.trim();

  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }
  if (trimmed.startsWith('data:image/')) {
    return trimmed;
  }

  const md = trimmed.match(/!\[[^\]]*\]\((https?:[^)\s]+)\)/);
  if (md) {
    return md[1];
  }

  try {
    const parsed = JSON.parse(trimmed);
    const fromObj = extractFromObject(parsed);
    if (fromObj) return fromObj;
  } catch {
    // not JSON
  }

  const loose = trimmed.match(/https?:\/\/[^\s"'<>[\]()]+/);
  if (loose) {
    return loose[0].replace(/[),.;]+$/, '');
  }

  return null;
}

function extractFromObject(obj) {
  if (!obj || typeof obj !== 'object') return null;

  const keys = ['resultObj', 'url', 'imageUrl', 'image', 'src', 'href', 'data'];
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === 'string') {
      if (/^https?:\/\//i.test(v) || v.startsWith('data:image/')) {
        return v;
      }
    }
  }

  if (obj.result && typeof obj.result === 'object') {
    const nested = extractFromObject(obj.result);
    if (nested) return nested;
  }

  return null;
}

/**
 * AntV MCP 等图表工具名称识别（与具体工具名弱耦合）
 * @param {string} name
 */
export function isChartLikeToolName(name) {
  const n = (name || '').toLowerCase();
  if (!n) return false;
  if (n.includes('chart')) return true;
  if (n.startsWith('generate_')) return true;
  if (n.includes('spreadsheet')) return true;
  if (n.includes('word_cloud')) return true;
  if (n.includes('mind_map') || n.includes('mind-map')) return true;
  if (n.includes('fishbone') || n.includes('flow_diagram') || n.includes('flow-diagram')) return true;
  if (n.includes('venn') || n.includes('sankey') || n.includes('treemap')) return true;
  if (n.includes('network_graph') || n.includes('organization_chart')) return true;
  if (n.includes('_map') && n.includes('generate')) return true;
  return false;
}
