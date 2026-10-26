import ELK from 'elkjs/lib/elk.bundled.js';

export interface GNode { id: string; group?: string; title: string; detail?: string; tone?: string; kind?: string; style?: string; mono?: boolean }
export interface GEdge { from: string; to: string; label?: string; style?: string; back?: boolean }
export interface Graph { id: string; alt: string; title?: string; direction?: string; layout?: string; nodeGap?: number; layerGap?: number; legend?: [string, string][]; groups?: { id: string; label: string; tone?: string }[]; nodes: GNode[]; edges: GEdge[] }
export interface Opts { layout: string; dir?: string; layerGap?: string; nodeGap?: string; padY?: number; placement?: string }
export type Box = { x: number; y: number; w: number; h: number };
export type Measure = (text: string, role: 'title' | 'titleMono' | 'detail' | 'edge' | 'group') => { w: number; h: number };
// A group's box must be wide enough for its heading: inset, mask padding, and the right-hand margin.
const headingWidth = (m: Measure, label: string) => Math.ceil(m(label, 'group').w + 40);

// Node sizes from measured text, then ring or ELK layered placement.
export async function layoutGraph(g: Graph, o: Opts, m: Measure) {
  const padY = o.padY ?? 18;
  const sizes = new Map<string, { w: number; h: number; t: { w: number; h: number }; d?: { w: number; h: number } }>();
  for (const n of g.nodes) {
    const t = m(n.title, n.mono ? 'titleMono' : 'title');
    const d = n.detail ? m(n.detail, 'detail') : undefined;
    const padX = n.kind === 'actor' ? 30 : 22;
    const w = Math.max(150, Math.ceil(Math.max(t.w, d?.w || 0) + 2 * padX));
    const h = Math.ceil(padY + t.h + (d ? 4 + d.h : 0) + padY);
    sizes.set(n.id, { w, h, t, d });
  }
  const pos = new Map<string, { x: number; y: number; w: number; h: number }>();
  const groupBoxes = new Map<string, { x: number; y: number; w: number; h: number }>();
  const edgePaths: { e: GEdge; pts: [number, number][]; label?: { x: number; y: number } }[] = [];

  if (o.layout.startsWith('ring')) {
    // Cycle: first half left to right on top, second half right to left below, return edge up the left side.
    const n = g.nodes.length, top = Math.ceil(n / 2);
    const w = Math.max(...[...sizes.values()].map(s => s.w)), h = Math.max(...[...sizes.values()].map(s => s.h));
    const labelW = Math.max(0, ...g.edges.map(e => e.label ? m(e.label, 'edge').w : 0));
    const vertical = o.layout === 'ring-v', pad = 22, head = 34;
    // Horizontal ring: rows of nodes; vertical ring: two columns, so the drawing fits the 860px column.
    const gapX = vertical ? Math.ceil(labelW + 2 * pad + 48) : Math.max(90, Math.ceil(labelW + 36)), gapY = vertical ? 58 : 150;
    g.nodes.forEach((node, i) => {
      const a = i < top ? i : n - 1 - i, b = i < top ? 0 : 1;
      const [col, row] = vertical ? [b, a] : [a, b];
      pos.set(node.id, { x: pad + col * (w + gapX), y: head + row * (h + gapY), w, h });
    });
    for (const grp of g.groups || []) {
      const members = g.nodes.filter(x => x.group === grp.id).map(x => pos.get(x.id)!);
      const x0 = Math.min(...members.map(p => p.x)) - pad, y0 = Math.min(...members.map(p => p.y)) - head;
      const x1 = Math.max(...members.map(p => p.x + p.w)) + pad, y1 = Math.max(...members.map(p => p.y + p.h)) + pad;
      groupBoxes.set(grp.id, { x: x0, y: y0, w: Math.max(x1 - x0, headingWidth(m, grp.label)), h: y1 - y0 });
    }
    for (const e of g.edges) {
      const a = pos.get(e.from)!, b = pos.get(e.to)!;
      if (Math.abs(a.y - b.y) < 1) {
        const rightward = b.x > a.x, y = a.y + a.h / 2;
        const x0 = rightward ? a.x + a.w : a.x, x1 = rightward ? b.x : b.x + b.w;
        const lw = e.label ? m(e.label, 'edge') : { w: 0, h: 0 };
        edgePaths.push({ e, pts: [[x0, y], [x1, y]], label: e.label ? { x: (x0 + x1) / 2 - lw.w / 2, y: y - lw.h - 8 } : undefined });
      } else if (Math.abs(a.x - b.x) < 1) {
        const down = b.y > a.y, x = a.x + a.w / 2;
        const y0 = down ? a.y + a.h : a.y, y1 = down ? b.y : b.y + b.h;
        const lw = e.label ? m(e.label, 'edge') : { w: 0, h: 0 };
        edgePaths.push({ e, pts: [[x, y0], [x, y1]], label: e.label ? { x: x + 12, y: (y0 + y1) / 2 - lw.h / 2 } : undefined });
      } else {
        // Odd-sized rings offset the two halves, so the crossover changes both coordinates: route an elbow.
        const lw = e.label ? m(e.label, 'edge') : { w: 0, h: 0 };
        if (vertical) {
          const rightward = b.x > a.x, x0 = rightward ? a.x + a.w : a.x, x1 = rightward ? b.x : b.x + b.w, mx = (x0 + x1) / 2;
          const y0 = a.y + a.h / 2, y1 = b.y + b.h / 2;
          edgePaths.push({ e, pts: [[x0, y0], [mx, y0], [mx, y1], [x1, y1]], label: e.label ? { x: mx - lw.w / 2, y: Math.min(y0, y1) - lw.h - 8 } : undefined });
        } else {
          const down = b.y > a.y, y0 = down ? a.y + a.h : a.y, y1 = down ? b.y : b.y + b.h, my = (y0 + y1) / 2;
          const x0 = a.x + a.w / 2, x1 = b.x + b.w / 2;
          edgePaths.push({ e, pts: [[x0, y0], [x0, my], [x1, my], [x1, y1]], label: e.label ? { x: Math.max(x0, x1) + 12, y: my - lw.h - 4 } : undefined });
        }
      }
    }
  } else {
    const elk = new ELK();
    const nodeOf = (n: GNode) => ({ id: n.id, width: sizes.get(n.id)!.w, height: sizes.get(n.id)!.h });
    const children: any[] = g.nodes.filter(n => !n.group).map(nodeOf);
    for (const grp of g.groups || []) {
      children.push({ id: `group:${grp.id}`, layoutOptions: { 'elk.padding': '[top=44,left=22,bottom=22,right=22]' }, children: g.nodes.filter(n => n.group === grp.id).map(nodeOf) });
    }
    const edges = g.edges.map((e, i) => ({ id: `e${i}`, sources: [e.from], targets: [e.to], labels: e.label ? [{ text: e.label, ...(({ w, h }) => ({ width: w + 8, height: h }))(m(e.label, 'edge')) }] : [] }));
    const laid = await elk.layout({ id: 'root', children, edges, layoutOptions: {
      'elk.algorithm': 'layered', 'elk.direction': o.dir || g.direction || 'RIGHT', 'elk.hierarchyHandling': 'INCLUDE_CHILDREN',
      'elk.edgeRouting': 'ORTHOGONAL', 'elk.json.edgeCoords': 'ROOT', 'elk.json.shapeCoords': 'ROOT',
      'elk.spacing.nodeNode': o.nodeGap || '44', 'elk.layered.spacing.nodeNodeBetweenLayers': o.layerGap || '64', 'elk.spacing.edgeNode': '22',
      'elk.layered.spacing.edgeNodeBetweenLayers': '22', 'elk.spacing.edgeEdge': '14', 'elk.spacing.edgeLabel': '6',
      'elk.edgeLabels.placement': 'CENTER', 'elk.layered.nodePlacement.strategy': o.placement || 'NETWORK_SIMPLEX', 'elk.layered.nodePlacement.bk.fixedAlignment': 'BALANCED',
      'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES', 'elk.layered.mergeEdges': 'false', 'elk.layered.crossingMinimization.forceNodeModelOrder': 'true', 'elk.portConstraints': 'FREE',
    } });
    // Match generated group ids exactly; a node id may look like one, and diagram.ts rejects the prefix too.
    const groupIds = new Set((g.groups || []).map(grp => `group:${grp.id}`));
    const walk = (node: any) => {
      for (const c of node.children || []) {
        if (groupIds.has(c.id)) { groupBoxes.set(c.id.slice(6), { x: c.x, y: c.y, w: c.width, h: c.height }); walk(c); }
        else pos.set(c.id, { x: c.x, y: c.y, w: c.width, h: c.height });
      }
    };
    walk(laid);
    const pendingShifts: { edge: number; need: number }[] = [];
    // ELK's minimum-size option pads groups vertically, so widen a group narrower than its heading afterwards
    // and shift everything right of its old edge by the same amount; segments stay orthogonal.
    for (const grp of g.groups || []) {
      const b = groupBoxes.get(grp.id)!, need = headingWidth(m, grp.label) - b.w;
      if (need <= 0) continue;
      const edge = b.x + b.w - 0.5;
      for (const p of pos.values()) if (p.x >= edge) p.x += need;
      for (const [id, o] of groupBoxes) {
        if (id === grp.id) continue;
        if (o.x >= edge) o.x += need;
        else if (o.x + o.w > edge) o.w += need;
      }
      pendingShifts.push({ edge, need });
      b.w += need;
    }
    const pendingEdges: typeof edgePaths = [];
    for (const le of laid.edges || []) {
      const e = g.edges[Number(le.id.slice(1))];
      for (const s of le.sections || []) {
        const pts: [number, number][] = [[s.startPoint.x, s.startPoint.y], ...(s.bendPoints || []).map((p: any) => [p.x, p.y] as [number, number]), [s.endPoint.x, s.endPoint.y]];
        const l = le.labels?.[0];
        pendingEdges.push({ e, pts, label: l ? { x: l.x + 4, y: l.y } : undefined });
      }
    }
    for (const { edge, need } of pendingShifts) for (const ep of pendingEdges) {
      for (const pt of ep.pts) if (pt[0] >= edge) pt[0] += need;
      if (ep.label && ep.label.x >= edge) ep.label.x += need;
    }
    edgePaths.push(...pendingEdges);
  }

  // Bounds include routed edges and their labels, which ELK may place outside every node and group.
  const boxes: Box[] = [...pos.values(), ...groupBoxes.values()];
  for (const ep of edgePaths) {
    for (const [x, y] of ep.pts) boxes.push({ x, y, w: 0, h: 0 });
    if (ep.label && ep.e.label) { const t = m(ep.e.label, 'edge'); boxes.push({ x: ep.label.x, y: ep.label.y, w: t.w, h: t.h }); }
  }
  const x0 = Math.min(...boxes.map(b => b.x)), y0 = Math.min(...boxes.map(b => b.y));
  const x1 = Math.max(...boxes.map(b => b.x + b.w)), y1 = Math.max(...boxes.map(b => b.y + b.h));
  return { sizes, pos, groupBoxes, edgePaths, bounds: { x0, y0, x1, y1 } };
}
