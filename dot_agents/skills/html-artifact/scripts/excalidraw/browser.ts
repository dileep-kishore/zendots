import { convertToExcalidrawElements, exportToSvg, FONT_FAMILY, serializeAsJSON } from '@excalidraw/excalidraw';

type Skeleton = NonNullable<Parameters<typeof convertToExcalidrawElements>[0]>[number];
interface Diagram { alt: string; elements: Skeleton[] }
interface Exported { light: string; dark: string; scene: string }
declare global { interface Window { exportDiagram: (diagram: Diagram) => Promise<Exported> } }

const palettes: Record<string, Record<string, string>> = {
  light: { ink: '#4c4f69', surface: '#e6e9ef', accent: '#8839ef', blue: '#1e66f5', green: '#40a02b', peach: '#fe640b', yellow: '#df8e1d', red: '#d20f39', teal: '#179299' },
  dark: { ink: '#cdd6f4', surface: '#181825', accent: '#cba6f7', blue: '#89b4fa', green: '#a6e3a1', peach: '#fab387', yellow: '#f9e2af', red: '#f38ba8', teal: '#94e2d5' },
};

window.exportDiagram = async (diagram) => {
  const result = {} as Exported;
  // Export a font subset first so real labels are measured with the embedded font.
  const text = diagram.elements.map(el => 'text' in el ? el.text : 'label' in el ? el.label?.text : '').join('\n');
  const probe = convertToExcalidrawElements([{ type: 'text', x: 0, y: 0, text: text || 'Diagram', fontFamily: FONT_FAMILY.Excalifont }]);
  const fontSvg = await exportToSvg({ elements: probe, appState: { exportBackground: false }, files: {} });
  const style = document.createElement('style');
  style.textContent = fontSvg.querySelector('style')?.textContent || '';
  if (!style.textContent.includes('data:font/')) throw new Error('Excalifont did not embed');
  document.head.append(style);
  await document.fonts.load('24px Excalifont', text || 'Diagram');

  for (const mode of ['light', 'dark'] as const) {
    const palette = palettes[mode];
    const themed: Skeleton[] = JSON.parse(JSON.stringify(diagram.elements, (key, value) => {
      if (['strokeColor', 'backgroundColor'].includes(key) && typeof value === 'string' && value.startsWith('$')) {
        const color = palette[value.slice(1)];
        if (!color) throw new Error(`Unknown palette token: ${value}`);
        return color;
      }
      return value;
    }));
    const elements = convertToExcalidrawElements(themed.map((el, index) => ({
      strokeColor: palette.ink, backgroundColor: 'transparent', roughness: 1,
      strokeWidth: 1.5, fontSize: 24, ...el, id: el.id || `element-${index}`,
      fontFamily: FONT_FAMILY.Excalifont,
      ...('label' in el && el.label ? { label: { fontSize: 24, strokeColor: palette.ink, ...el.label, fontFamily: FONT_FAMILY.Excalifont } } : {}),
    })), { regenerateIds: false }).map((el, index) => ({ ...el, seed: 1000 + index, updated: 1 }));
    const appState = { exportBackground: false, exportWithDarkMode: false, viewBackgroundColor: palette.surface };
    result[mode] = (await exportToSvg({ elements, appState, files: {}, exportPadding: 28 })).outerHTML;
    if (mode === 'light') result.scene = serializeAsJSON(elements, { ...appState, theme: 'light' }, {}, 'local');
  }
  return result;
};
