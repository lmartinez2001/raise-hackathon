import type { SVGProps } from "react"

export function Logo(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect x="4" y="8" width="20" height="20" rx="4" fill="#60A5FA" fillOpacity="0.6" />
      <rect x="8" y="4" width="20" height="20" rx="4" fill="#A78BFA" fillOpacity="0.6" />
      <g stroke="#1E293B" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none">
        <circle cx="16" cy="16" r="5" />
        <path d="M19.5 19.5 L 23 23" />
      </g>
    </svg>
  )
}
