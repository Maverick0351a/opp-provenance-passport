"use client";
import * as d3 from 'd3';
import { useEffect, useRef } from 'react';

export interface GraphProps {
  nodes: { id: string; ts?: string; step?: string }[];
  edges: { from: string; to: string; type?: string }[];
  width?: number;
  height?: number;
}

export function Graph({ nodes, edges, width = 640, height = 400 }: GraphProps) {
  const ref = useRef<SVGSVGElement | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll('*').remove();

    const sim = d3.forceSimulation(nodes as any)
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('link', d3.forceLink(edges as any).id((d: any) => d.id).distance(120))
      .force('collision', d3.forceCollide(40));

    const link = svg.append('g')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .selectAll('line')
      .data(edges)
      .enter().append('line')
      .attr('stroke-width', 1.5);

    const node = svg.append('g')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .selectAll('g')
      .data(nodes)
      .enter().append('g');

    node.append('circle')
      .attr('r', 16)
      .attr('fill', d => '#2d7aef');

    node.append('text')
      .text(d => (d.step || d.id.substring(0,6)))
      .attr('x', 20)
      .attr('y', 4)
      .attr('font-size', 10)
      .attr('font-family', 'system-ui, sans-serif');

    sim.on('tick', () => {
      link
        .attr('x1', (d: any) => (d.source as any).x)
        .attr('y1', (d: any) => (d.source as any).y)
        .attr('x2', (d: any) => (d.target as any).x)
        .attr('y2', (d: any) => (d.target as any).y);
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => { sim.stop(); };
  }, [nodes, edges, width, height]);
  return <svg ref={ref} width={width} height={height} />;
}

export default Graph;
