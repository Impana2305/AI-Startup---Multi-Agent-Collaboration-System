/* ------------------------------------------------------------------ */
/*  Startup Idea Input Form                                            */
/* ------------------------------------------------------------------ */

"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import type { StartupIdea } from "@/lib/types";
import { uploadPDF } from "@/lib/api";

interface StartupFormProps {
  onSubmit: (data: StartupIdea) => void;
  isLoading: boolean;
}

const INDUSTRIES = [
  "AI / Machine Learning",
  "FinTech",
  "HealthTech",
  "EdTech",
  "E-Commerce",
  "SaaS",
  "CleanTech",
  "BioTech",
  "Gaming",
  "Cybersecurity",
  "AgriTech",
  "PropTech",
  "Other",
];

const FUNDING_STAGES = [
  "Pre-seed",
  "Seed",
  "Series A",
  "Series B",
  "Series C+",
  "Bootstrapped",
];

export default function StartupForm({ onSubmit, isLoading }: StartupFormProps) {
  const [form, setForm] = useState<StartupIdea>({
    startup_idea: "",
    problem_statement: "",
    solution: "",
    target_customers: "",
    revenue_model: "",
    industry: "",
    funding_stage: "",
    pitch_deck_text: "",
    business_plan_text: "",
    website_url: "",
  });

  const [pitchFile, setPitchFile] = useState<string | null>(null);
  const [planFile, setPlanFile] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const pitchRef = useRef<HTMLInputElement>(null);
  const planRef = useRef<HTMLInputElement>(null);

  const update = (field: keyof StartupIdea, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handlePDF = async (
    file: File,
    field: "pitch_deck_text" | "business_plan_text",
    setName: (n: string) => void
  ) => {
    setUploading(true);
    try {
      const result = await uploadPDF(file);
      update(field, result.extracted_text);
      setName(file.name);
    } catch (err) {
      console.error("PDF upload failed:", err);
    } finally {
      setUploading(false);
    }
  };

  const canSubmit =
    form.startup_idea &&
    form.problem_statement &&
    form.solution &&
    form.target_customers &&
    form.revenue_model &&
    form.industry &&
    form.funding_stage;

  return (
    <div className="min-h-screen flex items-center justify-center p-4 md:p-8">
      {/* Background gradient */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-[hsl(222,84%,5%)] via-[hsl(240,60%,8%)] to-[hsl(222,84%,5%)]" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
      </div>

      <Card className="w-full max-w-3xl glass-strong glow-cyan border-0">
        <CardHeader className="text-center pb-2">
          <div className="text-5xl mb-3">🏛️</div>
          <CardTitle className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
            AI Startup Boardroom
          </CardTitle>
          <p className="text-muted-foreground mt-2 text-sm">
            Submit your startup idea and watch 9 AI executives evaluate it in a
            live board meeting — with debate, conflict resolution, and voting.
          </p>
        </CardHeader>

        <CardContent className="space-y-5 pt-4">
          {/* Startup Idea */}
          <div className="space-y-2">
            <Label htmlFor="startup_idea" className="text-cyan-300 font-medium">
              Startup Idea *
            </Label>
            <Input
              id="startup_idea"
              placeholder="e.g. AI-powered personal nutrition coach using computer vision"
              value={form.startup_idea}
              onChange={(e) => update("startup_idea", e.target.value)}
              className="bg-secondary/50 border-secondary focus:border-cyan-500/50"
            />
          </div>

          {/* Problem Statement */}
          <div className="space-y-2">
            <Label htmlFor="problem" className="text-cyan-300 font-medium">
              Problem Statement *
            </Label>
            <Textarea
              id="problem"
              placeholder="What problem does your startup solve?"
              value={form.problem_statement}
              onChange={(e) => update("problem_statement", e.target.value)}
              rows={3}
              className="bg-secondary/50 border-secondary focus:border-cyan-500/50"
            />
          </div>

          {/* Solution */}
          <div className="space-y-2">
            <Label htmlFor="solution" className="text-cyan-300 font-medium">
              Solution *
            </Label>
            <Textarea
              id="solution"
              placeholder="How does your startup solve the problem?"
              value={form.solution}
              onChange={(e) => update("solution", e.target.value)}
              rows={3}
              className="bg-secondary/50 border-secondary focus:border-cyan-500/50"
            />
          </div>

          {/* Target Customers */}
          <div className="space-y-2">
            <Label htmlFor="customers" className="text-cyan-300 font-medium">
              Target Customers *
            </Label>
            <Input
              id="customers"
              placeholder="Who are your target customers?"
              value={form.target_customers}
              onChange={(e) => update("target_customers", e.target.value)}
              className="bg-secondary/50 border-secondary focus:border-cyan-500/50"
            />
          </div>

          {/* Revenue Model */}
          <div className="space-y-2">
            <Label htmlFor="revenue" className="text-cyan-300 font-medium">
              Revenue Model *
            </Label>
            <Input
              id="revenue"
              placeholder="e.g. SaaS subscription, Freemium, Marketplace commission"
              value={form.revenue_model}
              onChange={(e) => update("revenue_model", e.target.value)}
              className="bg-secondary/50 border-secondary focus:border-cyan-500/50"
            />
          </div>

          {/* Industry & Funding Stage */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-cyan-300 font-medium">Industry *</Label>
              <div className="flex flex-wrap gap-2">
                {INDUSTRIES.map((ind) => (
                  <Badge
                    key={ind}
                    variant={form.industry === ind ? "default" : "outline"}
                    className={`cursor-pointer transition-all ${
                      form.industry === ind
                        ? "bg-cyan-600 hover:bg-cyan-700 border-cyan-500"
                        : "hover:border-cyan-500/50 hover:text-cyan-300"
                    }`}
                    onClick={() => update("industry", ind)}
                  >
                    {ind}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-cyan-300 font-medium">
                Funding Stage *
              </Label>
              <div className="flex flex-wrap gap-2">
                {FUNDING_STAGES.map((stage) => (
                  <Badge
                    key={stage}
                    variant={form.funding_stage === stage ? "default" : "outline"}
                    className={`cursor-pointer transition-all ${
                      form.funding_stage === stage
                        ? "bg-purple-600 hover:bg-purple-700 border-purple-500"
                        : "hover:border-purple-500/50 hover:text-purple-300"
                    }`}
                    onClick={() => update("funding_stage", stage)}
                  >
                    {stage}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Optional: Website URL */}
          <div className="space-y-2">
            <Label htmlFor="website" className="text-muted-foreground font-medium">
              Website URL (optional)
            </Label>
            <Input
              id="website"
              placeholder="https://your-startup.com"
              value={form.website_url || ""}
              onChange={(e) => update("website_url", e.target.value)}
              className="bg-secondary/50 border-secondary focus:border-cyan-500/50"
            />
          </div>

          {/* Optional: PDF Uploads */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-muted-foreground font-medium">
                Pitch Deck PDF (optional)
              </Label>
              <input
                ref={pitchRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handlePDF(file, "pitch_deck_text", setPitchFile);
                }}
              />
              <Button
                variant="outline"
                className="w-full justify-start text-muted-foreground hover:text-cyan-300 hover:border-cyan-500/50"
                onClick={() => pitchRef.current?.click()}
                disabled={uploading}
              >
                {pitchFile ? `✅ ${pitchFile}` : "📄 Upload Pitch Deck"}
              </Button>
            </div>

            <div className="space-y-2">
              <Label className="text-muted-foreground font-medium">
                Business Plan PDF (optional)
              </Label>
              <input
                ref={planRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handlePDF(file, "business_plan_text", setPlanFile);
                }}
              />
              <Button
                variant="outline"
                className="w-full justify-start text-muted-foreground hover:text-cyan-300 hover:border-cyan-500/50"
                onClick={() => planRef.current?.click()}
                disabled={uploading}
              >
                {planFile ? `✅ ${planFile}` : "📄 Upload Business Plan"}
              </Button>
            </div>
          </div>

          {/* Submit */}
          <Button
            className="w-full h-12 text-lg font-semibold bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-600 hover:to-purple-700 transition-all duration-300 shadow-lg shadow-cyan-500/20"
            disabled={!canSubmit || isLoading}
            onClick={() => onSubmit(form)}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">⏳</span> Convening the Board…
              </span>
            ) : (
              "🏛️ Start Board Meeting"
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
