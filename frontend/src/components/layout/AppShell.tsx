"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { DatabaseZap, FileSearch, GitBranchPlus, Network, Shield, Sparkles, Workflow } from "lucide-react";
import type { ReactNode } from "react";

const nav = [
  { href: "/", label: "Busca OSINT", icon: FileSearch },
  { href: "/investigations", label: "Investigações", icon: Workflow },
  { href: "/entities", label: "Entidades", icon: Sparkles },
  { href: "/relations", label: "Relações", icon: GitBranchPlus },
  { href: "/datasets", label: "Datasets", icon: DatabaseZap },
  { href: "/reports", label: "Relatórios", icon: Network },
  { href: "/admin", label: "Admin", icon: Shield }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="shell">
      <aside className="sidebar glass">
        <div className="brand">
          <p className="brand-kicker">TransparenteGov</p>
          <h1>Investigação Pública</h1>
        </div>

        <nav className="nav-list">
          {nav.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link key={item.href} className={`nav-item ${active ? "active" : ""}`} href={item.href}>
                <Icon size={16} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      <main className="content-wrap">
        <motion.div
          className="aurora"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.2 }}
        />
        <div className="content">{children}</div>
      </main>
    </div>
  );
}

