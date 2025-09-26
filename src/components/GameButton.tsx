import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GameButtonProps {
  children: ReactNode;
  variant?: "primary" | "secondary" | "success" | "warning";
  size?: "sm" | "md" | "lg";
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
}

export function GameButton({ 
  children, 
  variant = "primary", 
  size = "md", 
  className, 
  onClick, 
  disabled 
}: GameButtonProps) {
  const variantClasses = {
    primary: "bg-gradient-primary hover:shadow-glow border-primary/50 text-primary-foreground",
    secondary: "bg-gradient-secondary hover:shadow-glow border-secondary/50 text-secondary-foreground", 
    success: "bg-gradient-success hover:shadow-success border-success/50 text-success-foreground",
    warning: "bg-warning hover:shadow-glow border-warning/50 text-warning-foreground"
  };

  const sizeClasses = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg"
  };

  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "border-2 backdrop-blur-sm transition-all duration-300",
        "hover:scale-105 active:scale-95",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </Button>
  );
}