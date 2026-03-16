import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function formatTime(iso: string): string {
	return new Date(iso).toLocaleTimeString('es-UY', { hour: '2-digit', minute: '2-digit' });
}

export function formatDate(iso: string): string {
	const d = new Date(iso);
	const today = new Date();
	if (d.toDateString() === today.toDateString()) return 'Hoy';
	const yesterday = new Date(today);
	yesterday.setDate(today.getDate() - 1);
	if (d.toDateString() === yesterday.toDateString()) return 'Ayer';
	return d.toLocaleDateString('es-UY', { day: 'numeric', month: 'short' });
}

export function formatRelative(iso: string): string {
	const diff = Date.now() - new Date(iso).getTime();
	const mins = Math.floor(diff / 60000);
	if (mins < 1) return 'ahora';
	if (mins < 60) return `hace ${mins}m`;
	const hours = Math.floor(mins / 60);
	if (hours < 24) return `hace ${hours}h`;
	const days = Math.floor(hours / 24);
	if (days < 7) return `hace ${days}d`;
	return formatDate(iso);
}

export function initials(name: string | null): string {
	if (!name) return '?';
	return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
}

export const stageBadge: Record<string, string> = {
	new: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
	interested: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
	qualified: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
	negotiating: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
	visiting: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
	closing: 'bg-rose-500/15 text-rose-400 border-rose-500/20',
	won: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/20',
	lost: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/20',
};

export const priorityConfig: Record<string, { dot: string; text: string; label: string }> = {
	urgent: { dot: 'bg-red-400', text: 'text-red-400', label: 'Urgente' },
	high: { dot: 'bg-orange-400', text: 'text-orange-400', label: 'Alto' },
	medium: { dot: 'bg-amber-400', text: 'text-amber-400', label: 'Medio' },
	low: { dot: 'bg-zinc-500', text: 'text-zinc-400', label: 'Bajo' },
};

export const channelConfig: Record<string, { icon: string; color: string; label: string }> = {
	whatsapp: { icon: '💬', color: 'text-green-400', label: 'WhatsApp' },
	instagram_dm: { icon: '📸', color: 'text-pink-400', label: 'Instagram DM' },
	instagram_comment: { icon: '💬', color: 'text-pink-400', label: 'IG Comment' },
	web: { icon: '🌐', color: 'text-blue-400', label: 'Web' },
};
