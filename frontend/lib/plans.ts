import { buildApiUrl } from "./api";


export const SUBSCRIPTION_PLANS = [
  {
    code: "student",
    name: "Student",
    price: "$2.99/mo",
    description: "Affordable access for students building strong research habits.",
  },
  {
    code: "pro",
    name: "Pro",
    price: "$9.99/mo",
    description: "Best fit for frequent individual researchers using premium AI workflows.",
  },
  {
    code: "enterprise",
    name: "Enterprise",
    price: "$14.99/mo",
    description: "Team-ready foundation for labs, firms, and commercial research groups.",
  },
] as const;

export function getPlanCheckoutUrl(planCode: string): string {
  return buildApiUrl(`/plans/${planCode}`);
}
