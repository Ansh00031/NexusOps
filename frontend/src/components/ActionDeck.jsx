import React, { useState } from 'react';
import { 
  Check, 
  X, 
  RotateCcw, 
  ShieldCheck, 
  ShieldAlert, 
  DollarSign, 
  Layers, 
  Cpu, 
  Server, 
  MessageSquare,
  AlertTriangle,
  Play
} from 'lucide-react';

export default function ActionDeck({ 
  incidentId, 
  actions, 
  onApprove, 
  onReject, 
  onApproveSafe, 
  onRollback 
}) {
  const [commentModal, setCommentModal] = useState(null); // { actionId, type: 'approve' | 'reject' }
  const [managerComment, setManagerComment] = useState('');
  const [processingId, setProcessingId] = useState(null);

  if (!actions || actions.length === 0) return null;

  const safeActionsCount = actions.filter(a => !a.requires_approval && a.status === 'pending').length;

  const handleOpenComment = (actionId, type) => {
    setCommentModal({ actionId, type });
    setManagerComment('');
  };

  const handleConfirmAction = async () => {
    if (!commentModal) return;
    const { actionId, type } = commentModal;
    setProcessingId(actionId);
    try {
      if (type === 'approve') {
        await onApprove(actionId, managerComment);
      } else {
        await onReject(actionId, managerComment);
      }
    } finally {
      setProcessingId(null);
      setCommentModal(null);
      setManagerComment('');
    }
  };

  const handleRollback = async (actionId) => {
    setProcessingId(actionId);
    try {
      await onRollback(actionId);
    } finally {
      setProcessingId(null);
    }
  };

  const getDeptColor = (dept) => {
    switch (dept) {
      case 'IT': return 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30';
      case 'FINANCE': return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
      case 'INVENTORY': return 'bg-amber-500/10 text-amber-300 border-amber-500/30';
      case 'SECURITY': return 'bg-rose-500/10 text-rose-300 border-rose-500/30';
      default: return 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30';
    }
  };

  return (
    <div className="p-4 rounded-xl border border-slate-800 bg-[#0d131f]/70 space-y-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-sm text-slate-100 uppercase tracking-wide">
              Proposed Departmental Actions
            </h3>
            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[11px] font-mono font-bold text-indigo-400">
              {actions.length} Actions
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Human-in-the-Loop review gates all high-stakes and financial operations.
          </p>
        </div>

        {/* Approve All Safe Actions Button */}
        {safeActionsCount > 0 && (
          <button
            onClick={() => onApproveSafe(incidentId)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-950 transition-all active:scale-95 self-start sm:self-auto"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Approve All Safe Actions ({safeActionsCount})</span>
          </button>
        )}
      </div>

      {/* Action Cards Deck */}
      <div className="space-y-3">
        {actions.map(action => {
          const isPending = action.status === 'pending';
          const isExecuted = action.status === 'executed-simulated';
          const isRejected = action.status === 'rejected';
          const isRolledBack = action.status === 'rolled-back';
          const isBusy = processingId === action.id;

          return (
            <div 
              key={action.id}
              className={`p-3.5 rounded-xl border transition-all ${
                isExecuted 
                  ? 'border-emerald-500/30 bg-emerald-950/10' 
                  : isRejected 
                  ? 'border-slate-800/60 bg-slate-900/30 opacity-75' 
                  : isRolledBack
                  ? 'border-slate-800 bg-slate-900/40 opacity-75'
                  : action.requires_approval
                  ? 'border-rose-500/30 bg-rose-950/10 hover:border-rose-500/50'
                  : 'border-slate-700 bg-slate-900/60 hover:border-indigo-500/40'
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                {/* Department badge & Action Name */}
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider font-mono ${getDeptColor(action.department)}`}>
                      {action.department}
                    </span>
                    <h5 className="text-xs font-bold text-white tracking-tight">
                      {action.type.replace(/_/g, ' ').toUpperCase()} • <span className="font-mono text-indigo-300">{action.target}</span>
                    </h5>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {action.rationale}
                  </p>
                </div>

                {/* Status Indicator & Financial Impact */}
                <div className="flex flex-col items-end space-y-1 flex-shrink-0">
                  {action.financial_impact > 0 && (
                    <span className="text-xs font-mono font-extrabold text-amber-400">
                      ${action.financial_impact.toLocaleString()}
                    </span>
                  )}

                  {isExecuted && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span>SIMULATED EXECUTED</span>
                    </span>
                  )}
                  {isRejected && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center space-x-1">
                      <X className="w-3 h-3 text-rose-400" />
                      <span>REJECTED</span>
                    </span>
                  )}
                  {isRolledBack && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700 flex items-center space-x-1">
                      <RotateCcw className="w-3 h-3" />
                      <span>ROLLED BACK</span>
                    </span>
                  )}
                  {isPending && action.requires_approval && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center space-x-1">
                      <ShieldAlert className="w-3 h-3 text-amber-400" />
                      <span>REQUIRES APPROVAL</span>
                    </span>
                  )}
                  {isPending && !action.requires_approval && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      <span>SAFE / AUTO-APPROVABLE</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Guardrail Trigger Banner if applicable */}
              {action.guardrail_trigger && isPending && (
                <div className="mb-2.5 p-2 rounded bg-rose-950/40 border border-rose-500/30 text-[11px] text-rose-300 flex items-center space-x-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                  <span>{action.guardrail_trigger}</span>
                </div>
              )}

              {/* Execution details if executed */}
              {action.execution_result && (
                <div className="mb-2.5 p-2 rounded bg-emerald-950/30 border border-emerald-500/20 text-[11px] font-mono text-emerald-300">
                  {action.execution_result.message || 'Action executed against stateful enterprise database.'}
                </div>
              )}

              {/* Manager comment if rejected or approved */}
              {action.manager_comment && (
                <div className="mb-2.5 p-2 rounded bg-slate-800/80 text-[11px] text-slate-300 italic flex items-center space-x-1.5">
                  <MessageSquare className="w-3 h-3 text-slate-400" />
                  <span>Manager Note: "{action.manager_comment}"</span>
                </div>
              )}

              {/* Actions Footer Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800/60">
                {isPending && (
                  <>
                    <button
                      disabled={isBusy}
                      onClick={() => handleOpenComment(action.id, 'reject')}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold text-rose-400 hover:bg-rose-500/10 border border-rose-500/30 hover:border-rose-500/60 transition-all active:scale-95 disabled:opacity-50"
                    >
                      Reject
                    </button>
                    <button
                      disabled={isBusy}
                      onClick={() => handleOpenComment(action.id, 'approve')}
                      className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-md shadow-emerald-950 transition-all active:scale-95 disabled:opacity-50 flex items-center space-x-1"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Approve & Execute (Simulated)</span>
                    </button>
                  </>
                )}

                {isExecuted && action.reversibility && (
                  <button
                    disabled={isBusy}
                    onClick={() => handleRollback(action.id)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-amber-400 hover:bg-amber-500/10 border border-amber-500/30 hover:border-amber-500/60 transition-all active:scale-95 disabled:opacity-50"
                    title="Reverts simulated state in SQLite database"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Rollback Simulated State</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Manager Comment & Confirmation Modal */}
      {commentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#111827] border border-slate-700 rounded-xl p-5 w-full max-w-md shadow-2xl space-y-4">
            <h4 className="font-bold text-sm text-white">
              {commentModal.type === 'approve' ? 'Approve & Execute Action' : 'Reject Proposed Action'}
            </h4>
            <p className="text-xs text-slate-300">
              {commentModal.type === 'approve' 
                ? 'This action will be executed against the stateful enterprise simulator. Add an optional operational audit comment:' 
                : 'Provide a reason for rejecting this proposed agent action for the audit record:'}
            </p>
            <textarea
              rows={3}
              value={managerComment}
              onChange={(e) => setManagerComment(e.target.value)}
              placeholder="e.g., Approved as client is Tier-1 VIP under contract SLA 99.99%."
              className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setCommentModal(null)}
                className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmAction}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold text-white ${
                  commentModal.type === 'approve' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-rose-600 hover:bg-rose-500'
                }`}
              >
                {commentModal.type === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
