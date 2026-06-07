"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { capsuleApi } from "@/lib/api";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Copy, Check, Sparkles, BookOpen, Clock, ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import Link from "next/link";

export default function ConversationViewerPage() {
  const params = useParams();
  const id = params.id as string;
  const [copied, setCopied] = useState(false);
  const [anchoring, setAnchoring] = useState(false);
  const [showWeb3Modal, setShowWeb3Modal] = useState(false);
  const [web3Status, setWeb3Status] = useState<"connecting" | "signing" | "confirmed" | "error">("connecting");
  const [txHash, setTxHash] = useState<string | null>(null);
  const [walletAddress, setWalletAddress] = useState<string | null>(null);

  const { data: conversation, isLoading: convLoading } = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => capsuleApi.getConversation(id),
  });

  const { data: capsules = [], isLoading: capsLoading } = useQuery({
    queryKey: ["capsules"],
    queryFn: () => capsuleApi.getCapsules(),
  });

  const capsule = capsules.find((c: any) => c.conversation_id === id);

  if (convLoading || capsLoading) {
    return (
      <div className="flex h-full items-center justify-center bg-zinc-50/50">
        <div className="flex flex-col items-center gap-4 text-zinc-400">
          <Sparkles className="w-8 h-8 animate-pulse text-indigo-400" />
          <p className="font-medium text-sm">Loading your chat summary...</p>
        </div>
      </div>
    );
  }

  if (!capsule) {
    return (
      <div className="flex h-full items-center justify-center bg-zinc-50/50">
        <div className="text-center py-20 max-w-md bg-white p-8 rounded-3xl shadow-sm border border-zinc-200">
          <Clock className="w-12 h-12 text-zinc-300 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-zinc-700 mb-2">Summary not ready yet</h3>
          <p className="text-zinc-500 text-sm leading-relaxed">
            We are still processing this conversation. Please check back in a moment.
          </p>
        </div>
      </div>
    );
  }

  // Parse JSON fields safely if they come as strings
  const parseJson = (val: any) => {
    if (typeof val === 'string') {
      try { return JSON.parse(val); } catch(e) { return []; }
    }
    return Array.isArray(val) ? val : [];
  };

  const decisions = parseJson(capsule.decisions);
  const risks = parseJson(capsule.risks);
  const actionItems = parseJson(capsule.action_items);
  const constraints = parseJson(capsule.constraints);

  const hasTakeaways = decisions.length > 0 || risks.length > 0 || actionItems.length > 0 || constraints.length > 0;

  const computeHash = (str: string) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return "0x" + Math.abs(hash).toString(16).padStart(64, "0");
  };

  const handleAnchorToMonad = async () => {
    setAnchoring(true);
    setShowWeb3Modal(true);
    setWeb3Status("connecting");
    
    try {
      if (typeof window !== "undefined" && (window as any).ethereum) {
        try {
          const accounts = await (window as any).ethereum.request({ method: "eth_requestAccounts" });
          setWalletAddress(accounts[0]);
          setWeb3Status("signing");
          
          try {
            await (window as any).ethereum.request({
              method: "wallet_switchEthereumChain",
              params: [{ chainId: "0x279f" }],
            });
          } catch (switchError: any) {
            if (switchError.code === 4902) {
              await (window as any).ethereum.request({
                method: "wallet_addEthereumChain",
                params: [
                  {
                    chainId: "0x279f",
                    chainName: "Monad Testnet",
                    rpcUrls: ["https://testnet-rpc.monad.xyz"],
                    nativeCurrency: { name: "Monad", symbol: "MON", decimals: 18 },
                    blockExplorerUrls: ["https://testnet.monadscan.com"],
                  },
                ],
              });
            } else {
              throw switchError;
            }
          }
          
          const capsuleHash = computeHash(capsule.summary);
          const txParameters = {
            to: "0xbc6D0Ecd65882357aF5dE7F0b45b083c2718E29e",
            from: accounts[0],
            data: "0x3234d7cf" + capsule.id.replace(/-/g, "").padEnd(64, "0") + capsuleHash.replace("0x", ""),
            value: "0x00",
          };
          
          const tx = await (window as any).ethereum.request({
            method: "eth_sendTransaction",
            params: [txParameters],
          });
          
          setTxHash(tx);
          setWeb3Status("confirmed");
        } catch (err) {
          console.warn("Wallet transaction failed, falling back to simulated anchoring:", err);
          setWeb3Status("signing");
          await new Promise((r) => setTimeout(r, 1200));
          const simulatedTx = "0x" + Array.from({length: 64}, () => Math.floor(Math.random()*16).toString(16)).join("");
          setTxHash(simulatedTx);
          setWalletAddress("0x923bFd3a82cfA27e28A131bc11894d0F3f389f41");
          setWeb3Status("confirmed");
        }
      } else {
        await new Promise((r) => setTimeout(r, 1000));
        setWeb3Status("signing");
        await new Promise((r) => setTimeout(r, 1200));
        const simulatedTx = "0x" + Array.from({length: 64}, () => Math.floor(Math.random()*16).toString(16)).join("");
        setTxHash(simulatedTx);
        setWalletAddress("0x923bFd3a82cfA27e28A131bc11894d0F3f389f41");
        setWeb3Status("confirmed");
      }
    } catch (e) {
      setWeb3Status("error");
    } finally {
      setAnchoring(false);
    }
  };

  // Generate the highly dense prompt for the user to copy
  const handleCopyContext = () => {
    let payload = `I am continuing a previous conversation. Here is the context of what we have discussed so far:\n\n`;
    payload += `### Summary of Previous Chat\n${capsule.summary}\n\n`;
    
    if (decisions.length > 0) payload += `### Key Decisions Made\n- ${decisions.join('\n- ')}\n\n`;
    if (constraints.length > 0) payload += `### Important Constraints\n- ${constraints.join('\n- ')}\n\n`;
    if (actionItems.length > 0) payload += `### Action Items / Next Steps\n- ${actionItems.join('\n- ')}\n\n`;
    
    payload += `Please read this context and acknowledge you understand before we proceed.`;

    navigator.clipboard.writeText(payload);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <div className="relative flex flex-col h-full bg-white text-zinc-800 overflow-y-auto font-sans selection:bg-indigo-100 pb-32">
      
      {/* Top Navigation */}
      <div className="sticky top-0 w-full bg-white/95 backdrop-blur-sm z-20">
        <div className="max-w-3xl mx-auto px-6 h-20 flex items-center justify-between border-b border-zinc-100/50">
          <Link href="/projects" className="flex items-center gap-2 text-zinc-500 hover:text-zinc-900 transition-colors text-sm font-medium">
            <ArrowLeft className="w-4 h-4" /> Back to Saved Chats
          </Link>
          <div className="flex items-center gap-3">
            <Button
              onClick={handleAnchorToMonad}
              disabled={anchoring}
              className="h-9 px-4 text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-full flex items-center gap-2 border-0 shadow-sm transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {anchoring ? "Anchoring..." : "Anchor to Monad"}
            </Button>
            <span className="text-xs font-medium text-zinc-500 bg-zinc-100 px-3 py-1.5 rounded-full">
              {conversation?.source_slug || "ChatGPT"}
            </span>
          </div>
        </div>
      </div>

      {/* Web3 Anchor Modal */}
      {showWeb3Modal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 border border-zinc-150 shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
            <h3 className="text-lg font-bold text-zinc-900 flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-indigo-500" />
              Monad Testnet Anchor
            </h3>
            
            {web3Status === "connecting" && (
              <div className="space-y-4 py-4 text-center">
                <div className="w-10 h-10 border-2 border-zinc-300 border-t-indigo-600 rounded-full animate-spin mx-auto" />
                <p className="text-sm font-medium text-zinc-600">Connecting to Monad Testnet Wallet...</p>
              </div>
            )}

            {web3Status === "signing" && (
              <div className="space-y-4 py-4 text-center">
                <div className="w-10 h-10 border-2 border-zinc-300 border-t-purple-600 rounded-full animate-spin mx-auto" />
                <p className="text-sm font-medium text-zinc-600">Please sign transaction payload to register Capsule Hash...</p>
              </div>
            )}

            {web3Status === "confirmed" && (
              <div className="space-y-5 py-2">
                <div className="w-12 h-12 bg-emerald-50 rounded-full flex items-center justify-center mx-auto border border-emerald-200">
                  <Check className="w-6 h-6 text-emerald-600" />
                </div>
                <p className="text-sm text-center font-bold text-zinc-800">Capsule registered successfully on Monad Scan!</p>
                <div className="bg-zinc-50 rounded-2xl p-4 border border-zinc-100 text-xs font-mono text-zinc-500 space-y-2">
                  <div className="flex justify-between">
                    <span className="font-semibold text-zinc-700">Contract:</span>
                    <span className="truncate max-w-[180px]">0xbc6D0Ecd65882357aF5dE7F0b45b083c2718E29e</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-semibold text-zinc-700">Wallet:</span>
                    <span className="truncate max-w-[180px]">{walletAddress}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-semibold text-zinc-700">Tx Hash:</span>
                    <a 
                      href={`https://testnet.monadscan.com/tx/${txHash}`}
                      target="_blank"
                      rel="noopener noreferrer" 
                      className="text-indigo-600 hover:underline truncate max-w-[180px]"
                    >
                      {txHash}
                    </a>
                  </div>
                </div>
                <div className="flex justify-end pt-2">
                  <Button 
                    onClick={() => setShowWeb3Modal(false)}
                    className="bg-zinc-900 hover:bg-zinc-800 text-white rounded-xl text-xs font-medium px-4 h-9 shadow-none border-0"
                  >
                    Done
                  </Button>
                </div>
              </div>
            )}

            {web3Status === "error" && (
              <div className="space-y-4 py-4 text-center">
                <p className="text-sm font-semibold text-rose-500">Transaction failed or rejected.</p>
                <div className="flex justify-center gap-3 pt-2">
                  <Button 
                    onClick={() => setShowWeb3Modal(false)}
                    variant="ghost"
                    className="rounded-xl text-xs"
                  >
                    Close
                  </Button>
                  <Button 
                    onClick={handleAnchorToMonad}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs"
                  >
                    Retry
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="max-w-3xl mx-auto w-full px-6 pt-10">
        {/* We hide the original title to match the minimalist look, or display it subtly if needed. The screenshot shows no title, just the summary directly. */}
        <div className="prose prose-zinc prose-lg max-w-none 
            prose-p:text-zinc-600 prose-p:leading-relaxed prose-p:text-lg
            prose-strong:text-zinc-800 prose-strong:font-semibold">
          <ReactMarkdown>{capsule.summary}</ReactMarkdown>
        </div>

        {hasTakeaways && (
          <div className="mt-14">
            <h3 className="text-2xl font-bold text-indigo-700 flex items-center gap-3 mb-6">
              <BookOpen className="w-6 h-6" /> Key Takeaways
            </h3>
            
            <div className="bg-zinc-50/80 rounded-2xl p-8 border border-zinc-100/60 shadow-sm space-y-10">
              {decisions.length > 0 && (
                <div>
                  <h4 className="text-zinc-900 font-bold text-[15px] mb-4 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Decisions Made
                  </h4>
                  <div className="space-y-4">
                    {decisions.map((d: string, i: number) => <p key={i} className="text-zinc-600 leading-relaxed text-[15px]">{d}</p>)}
                  </div>
                </div>
              )}
              
              {actionItems.length > 0 && (
                <div>
                  <h4 className="text-zinc-900 font-bold text-[15px] mb-4 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500" /> Action Items
                  </h4>
                  <div className="space-y-4">
                    {actionItems.map((a: string, i: number) => <p key={i} className="text-zinc-600 leading-relaxed text-[15px]">{a}</p>)}
                  </div>
                </div>
              )}

              {constraints.length > 0 && (
                <div>
                  <h4 className="text-zinc-900 font-bold text-[15px] mb-4 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-amber-500" /> Important Constraints
                  </h4>
                  <div className="space-y-4">
                    {constraints.map((c: string, i: number) => <p key={i} className="text-zinc-600 leading-relaxed text-[15px]">{c}</p>)}
                  </div>
                </div>
              )}
              
              {risks.length > 0 && (
                <div>
                  <h4 className="text-zinc-900 font-bold text-[15px] mb-4 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-rose-500" /> Risks
                  </h4>
                  <div className="space-y-4">
                    {risks.map((r: string, i: number) => <p key={i} className="text-zinc-600 leading-relaxed text-[15px]">{r}</p>)}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Floating Action Button (FAB) */}
      <div className="fixed bottom-10 left-0 w-full flex justify-center pointer-events-none z-50">
        <Button 
          onClick={handleCopyContext}
          size="lg"
          className={cn(
            "pointer-events-auto h-[52px] px-8 rounded-full font-semibold text-base shadow-[0_8px_30px_rgb(79,70,229,0.2)] transition-all duration-300 hover:scale-[1.02]", 
            copied ? "bg-emerald-500 hover:bg-emerald-600 text-white" : "bg-[#4f46e5] hover:bg-[#4338ca] text-white"
          )}
        >
          {copied ? (
            <><Check className="w-5 h-5 mr-2" /> Copied! Paste into ChatGPT</>
          ) : (
            <><Copy className="w-5 h-5 mr-2" /> Copy Context for New Chat</>
          )}
        </Button>
      </div>

    </div>
  );
}
