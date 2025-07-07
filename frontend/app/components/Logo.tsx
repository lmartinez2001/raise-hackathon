import type { SVGProps } from "react"

export function Logo(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect x="4" y="8" width="20" height="20" rx="4" fill="#60A5FA" fillOpacity="0.6" />
      <rect x="8" y="4" width="20" height="20" rx="4" fill="#A78BFA" fillOpacity="0.6" />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M16.0002 20.6667C19.6821 20.6667 22.6668 17.6819 22.6668 14C22.6668 10.3181 19.6821 7.33333 16.0002 7.33333C12.3183 7.33333 9.3335 10.3181 9.3335 14C9.3335 17.6819 12.3183 20.6667 16.0002 20.6667ZM16.0002 23.3333C21.1504 23.3333 25.3335 19.1502 25.3335 14C25.3335 8.84974 21.1504 4.66666 16.0002 4.66666C10.85 4.66666 6.66683 8.84974 6.66683 14C6.66683 19.1502 10.85 23.3333 16.0002 23.3333Z"
        fill="#1E293B"
        fillOpacity="0.8"
      />
      <rect
        x="21.2"
        y="20.2"
        width="2.66667"
        height="6"
        rx="1.33333"
        transform="rotate(45 21.2 20.2)"
        fill="#1E293B"
        fillOpacity="0.8"
      />
    </svg>
  )
}
