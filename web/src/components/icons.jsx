// Small inline SVG icons — a formal replacement for emoji.

export function BrandMark({ size = 26 }) {
  // A stylized sugar-cane stalk with a leaf: on-theme but understated.
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="10.5" y="3" width="3" height="18" rx="1.5" fill="currentColor" />
      <line x1="10.5" y1="8" x2="13.5" y2="8" stroke="var(--brand-strong)" strokeWidth="1" />
      <line x1="10.5" y1="12" x2="13.5" y2="12" stroke="var(--brand-strong)" strokeWidth="1" />
      <line x1="10.5" y1="16" x2="13.5" y2="16" stroke="var(--brand-strong)" strokeWidth="1" />
      <path d="M13 7 C18 5, 20 8, 19 11 C15 11, 13 10, 13 7 Z" fill="currentColor" opacity="0.85" />
    </svg>
  );
}

export function BotIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="4" y="7" width="16" height="12" rx="3" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="9" cy="13" r="1.4" fill="currentColor" />
      <circle cx="15" cy="13" r="1.4" fill="currentColor" />
      <line x1="12" y1="4" x2="12" y2="7" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="3.2" r="1.2" fill="currentColor" />
    </svg>
  );
}

export function UserIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.6" />
      <path d="M4 20 C4 15.5, 8 14, 12 14 C16 14, 20 15.5, 20 20"
            stroke="currentColor" strokeWidth="1.6" fill="none" />
    </svg>
  );
}

export function SunIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.6" />
      <g stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
        <line x1="12" y1="2" x2="12" y2="4" /><line x1="12" y1="20" x2="12" y2="22" />
        <line x1="2" y1="12" x2="4" y2="12" /><line x1="20" y1="12" x2="22" y2="12" />
        <line x1="4.9" y1="4.9" x2="6.3" y2="6.3" /><line x1="17.7" y1="17.7" x2="19.1" y2="19.1" />
        <line x1="19.1" y1="4.9" x2="17.7" y2="6.3" /><line x1="6.3" y1="17.7" x2="4.9" y2="19.1" />
      </g>
    </svg>
  );
}

export function MoonIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M20 14.5 A8 8 0 1 1 9.5 4 A6.5 6.5 0 0 0 20 14.5 Z"
            stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinejoin="round" />
    </svg>
  );
}
