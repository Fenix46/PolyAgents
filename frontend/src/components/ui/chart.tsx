import * as React from "react";
import { cn } from "@/lib/utils";

// Simplified chart component for PolyAgents
export interface ChartProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

export const Chart = React.forwardRef<HTMLDivElement, ChartProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("chart-container", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Chart.displayName = "Chart";

export const ChartContainer = Chart;

export const ChartTooltip = ({ children }: { children?: React.ReactNode }) => {
  return <div className="chart-tooltip">{children}</div>;
};

export const ChartTooltipContent = ({ children }: { children?: React.ReactNode }) => {
  return <div className="chart-tooltip-content">{children}</div>;
};

export const ChartLegend = ({ children }: { children?: React.ReactNode }) => {
  return <div className="chart-legend">{children}</div>;
};

export const ChartLegendContent = ({ children }: { children?: React.ReactNode }) => {
  return <div className="chart-legend-content">{children}</div>;
};