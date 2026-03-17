const THEMES = {
	ocean: {
		label: 'Ocean',
		desc: 'Azul profundo + teal',
		base: '#0d1b27',
		surface: '#142e3f',
		elevated: '#1a3d52',
		border: 'rgba(37, 71, 103, 0.5)',
		borderSubtle: 'rgba(37, 71, 103, 0.3)',
		textPrimary: '#e6f1f5',
		textSecondary: '#9ab5c8',
		textTertiary: '#5d8099',
		textQuaternary: '#3d6080',
		accent: '#00d4aa',
		accentHover: '#00e6b8',
		accentMuted: 'rgba(0, 212, 170, 0.15)',
	},
	midnight: {
		label: 'Midnight Blue',
		desc: 'Estilo Linear/Discord',
		base: '#1a1d2e',
		surface: '#252a42',
		elevated: '#2f3555',
		border: 'rgba(58, 64, 102, 0.5)',
		borderSubtle: 'rgba(58, 64, 102, 0.3)',
		textPrimary: '#e8eaf6',
		textSecondary: '#a8aec8',
		textTertiary: '#6b729a',
		textQuaternary: '#4a4f72',
		accent: '#00d4aa',
		accentHover: '#00e6b8',
		accentMuted: 'rgba(0, 212, 170, 0.15)',
	},
	warm: {
		label: 'Warm Dark',
		desc: 'Estilo Notion/GitHub',
		base: '#1f1d1b',
		surface: '#2a2622',
		elevated: '#35302a',
		border: 'rgba(74, 66, 56, 0.5)',
		borderSubtle: 'rgba(74, 66, 56, 0.3)',
		textPrimary: '#e5dcd3',
		textSecondary: '#a89d8f',
		textTertiary: '#7a7060',
		textQuaternary: '#5a5040',
		accent: '#00d4aa',
		accentHover: '#00e6b8',
		accentMuted: 'rgba(0, 212, 170, 0.15)',
	},
} as const;

type ThemeKey = keyof typeof THEMES;

let current = $state<ThemeKey>((typeof localStorage !== 'undefined' ? localStorage.getItem('tabot:theme') as ThemeKey : null) || 'ocean');

export function getThemes() {
	return THEMES;
}

export function getThemeKey(): ThemeKey {
	return current;
}

export function setTheme(key: ThemeKey) {
	current = key;
	if (typeof localStorage !== 'undefined') {
		localStorage.setItem('tabot:theme', key);
	}
	applyTheme(key);
}

export function applyTheme(key?: ThemeKey) {
	const theme = THEMES[key || current];
	if (typeof document === 'undefined') return;

	const root = document.documentElement;
	root.style.setProperty('--color-base', theme.base);
	root.style.setProperty('--color-surface', theme.surface);
	root.style.setProperty('--color-elevated', theme.elevated);
	root.style.setProperty('--color-border', theme.border);
	root.style.setProperty('--color-border-subtle', theme.borderSubtle);
	root.style.setProperty('--color-text-primary', theme.textPrimary);
	root.style.setProperty('--color-text-secondary', theme.textSecondary);
	root.style.setProperty('--color-text-tertiary', theme.textTertiary);
	root.style.setProperty('--color-text-quaternary', theme.textQuaternary);
	root.style.setProperty('--color-accent', theme.accent);
	root.style.setProperty('--color-accent-hover', theme.accentHover);
	root.style.setProperty('--color-accent-muted', theme.accentMuted);

	document.body.style.backgroundColor = theme.base;
	document.body.style.color = theme.textPrimary;
}

export function initTheme() {
	applyTheme();
}
