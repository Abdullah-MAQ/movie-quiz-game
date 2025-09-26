import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GameCardProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "glow" | "success";
  hover?: boolean;
}

export function GameCard({ children, className, variant = "default", hover = true }: GameCardProps) {
  const variantClasses = {
    default: "bg-card/80 border-border",
    glow: "bg-card/80 border-primary/30 shadow-glow",
    success: "bg-card/80 border-success/30 shadow-success"
  };

  return (
    <Card
      className={cn(
        "backdrop-blur-lg transition-all duration-300",
        hover && "hover:scale-[1.02] hover:shadow-card",
        variantClasses[variant],
        className
      )}
    >
      {children}
    </Card>
  );
}