export interface VerificationLink {
  platform: string;
  title: string;
  url: string;
  tag: string;
  badge: string;
}

export function formatJobDescription(desc?: string): string {
  if (!desc) return "Opportunity details available via official careers portal.";
  let text = desc.replace(/<[^>]*>?/gm, " ");
  text = text.replace(/<[^>]*$/g, "");
  text = text.replace(/^Source:.*?\n(?:Role:.*?\n)?(?:Company:.*?\n)?(?:Details:\s*)?/i, "");
  text = text.replace(/[ \t]+/g, " ").replace(/\n\s*\n+/g, "\n\n").trim();
  return text || "Opportunity details available via official careers portal.";
}

export function getVerificationLinks(companyName?: string, roleTitle?: string): VerificationLink[] {
  if (!companyName) return [];
  const clean = companyName.trim();
  const encoded = encodeURIComponent(clean);
  const roleEncoded = roleTitle ? encodeURIComponent(roleTitle.trim()) : "";
  const linkedinJobQuery = roleEncoded ? `${encoded}+${roleEncoded}` : encoded;

  return [
    {
      platform: "LinkedIn Jobs",
      title: `${clean} Live Openings`,
      url: `https://www.linkedin.com/jobs/search/?keywords=${linkedinJobQuery}`,
      tag: "Live Recruiter Postings",
      badge: "border-blue-200 bg-blue-50 text-blue-800 hover:bg-blue-100"
    },
    {
      platform: "LinkedIn Network",
      title: `${clean} Alumni & Referrals`,
      url: `https://www.linkedin.com/search/results/people/?keywords=${encoded}&origin=GLOBAL_SEARCH_HEADER`,
      tag: "Alumni & Mentors",
      badge: "border-sky-200 bg-sky-50 text-sky-800 hover:bg-sky-100"
    },
    {
      platform: "Naukri",
      title: `${clean} Salaries & Demand`,
      url: `https://www.naukri.com/jobs-in-india?keyword=${encoded}`,
      tag: "Salaries & Trends",
      badge: "border-cyan-200 bg-cyan-50 text-cyan-800 hover:bg-cyan-100"
    },
    {
      platform: "GeeksforGeeks",
      title: `${clean} Student Experiences`,
      url: `https://www.geeksforgeeks.org/search/?q=${encoded}+interview+experience`,
      tag: "Real Campus Experiences",
      badge: "border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
    },
    {
      platform: "AmbitionBox",
      title: `${clean} Difficulty & Ratings`,
      url: `https://www.ambitionbox.com/search?q=${encoded}`,
      tag: "Interview Ratings & Reviews",
      badge: "border-indigo-200 bg-indigo-50 text-indigo-800 hover:bg-indigo-100"
    },
    {
      platform: "LeetCode Discuss",
      title: `${clean} Coding Questions`,
      url: `https://leetcode.com/discuss/interview-question?currentPage=1&orderBy=hot&query=${encoded}`,
      tag: "Algorithm Questions",
      badge: "border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100"
    }
  ];
}

