import 'package:flutter/material.dart';

import '../api/models.dart';
import '../theme/app_theme.dart';

// Employee-facing labels — deliberately separate from approval_queue_screen.dart's
// `_stageLabels` (which is approver/queue-phrased, e.g. "HOD queue"). The two
// label sets are independently editable; coupling them would risk one screen's
// copy change silently affecting the other.
const _employeeStageLabels = {
  'hod': 'HOD Review',
  'department_hod': 'Department HOD Review',
  'accountant': 'Accountant Review',
  'finance_manager': 'Finance Manager Review',
};

enum _StepState { done, current, rejected, upcoming }

class _Step {
  const _Step({required this.label, required this.state, this.caption, this.emphasizeCaption = false});

  final String label;
  final _StepState state;
  final String? caption;
  final bool emphasizeCaption;
}

/// Vertical stage tracker showing an employee exactly where their claim sits in
/// the approval pipeline (HOD → optional Department HOD → Accountant → Finance
/// Manager → Paid), with the dispute/reject reason surfaced inline on whichever
/// step sent it back. Vertical rather than horizontal: stage labels like
/// "Finance Manager Review" don't fit legibly side-by-side on phone width.
class ClaimStageTracker extends StatelessWidget {
  const ClaimStageTracker({super.key, required this.claim});

  final ExpenseClaim claim;

  /// Compact one-line label for list cards (e.g. My Claims), needing only
  /// `stageSequence` + `currentStage` — no history lookup required.
  static String? compactLabel(ExpenseClaim claim) {
    final seq = claim.stageSequence;
    final current = claim.currentStage;
    if (seq.isEmpty || current == null) return null;
    if (!seq.contains(current)) return null;
    final label = _employeeStageLabels[current] ?? current;
    return 'At $label';
  }

  List<_Step> _buildSteps() {
    final seq = claim.stageSequence;
    if (seq.isEmpty) return const [];

    // Last history action per stage — so a stage disputed once then approved
    // on resubmission shows done, not stuck on its old dispute.
    final lastActionForStage = <String, ClaimHistoryItem>{};
    for (final entry in claim.history ?? const <ClaimHistoryItem>[]) {
      if (entry.stage == null) continue;
      if (entry.action == 'approve' || entry.action == 'dispute' || entry.action == 'reject') {
        lastActionForStage[entry.stage!] = entry;
      }
    }

    final rejectedEntry = claim.status == 'rejected' ? claim.lastReturnEntry : null;
    final disputedEntry = claim.status == 'disputed' ? claim.lastReturnEntry : null;

    final steps = <_Step>[];
    for (final stage in seq) {
      final label = _employeeStageLabels[stage] ?? stage;

      if (rejectedEntry != null && rejectedEntry.stage == stage && rejectedEntry.action == 'reject') {
        steps.add(_Step(
          label: label,
          state: _StepState.rejected,
          caption: rejectedEntry.remarks,
          emphasizeCaption: true,
        ));
        break; // pipeline stopped here — nothing after renders
      }

      final lastAction = lastActionForStage[stage];
      if (lastAction?.action == 'approve') {
        steps.add(_Step(label: label, state: _StepState.done, caption: 'Approved'));
        continue;
      }

      if (claim.currentStage == stage) {
        if (disputedEntry != null) {
          steps.add(_Step(
            label: label,
            state: _StepState.current,
            caption: 'Sent back: ${disputedEntry.remarks ?? ''}',
            emphasizeCaption: true,
          ));
        } else {
          steps.add(_Step(label: label, state: _StepState.current, caption: 'Awaiting review'));
        }
        continue;
      }

      steps.add(_Step(label: label, state: _StepState.upcoming));
    }

    // Terminal "Paid" step — only reached if the pipeline wasn't cut short by rejection.
    if (rejectedEntry == null && (claim.status == 'approved' || claim.status == 'paid')) {
      for (var i = 0; i < steps.length; i++) {
        if (steps[i].state != _StepState.done) {
          steps[i] = _Step(label: steps[i].label, state: _StepState.done, caption: 'Approved');
        }
      }
      if (claim.status == 'paid') {
        final paidEntry = claim.history
            ?.lastWhere((e) => e.action == 'paid', orElse: () => const ClaimHistoryItem(id: -1, actorId: -1, action: ''));
        final caption = (paidEntry != null && paidEntry.id != -1)
            ? (paidEntry.createdAt != null && paidEntry.createdAt!.length >= 10
                ? 'Paid on ${paidEntry.createdAt!.substring(0, 10)}'
                : 'Paid')
            : 'Paid';
        steps.add(_Step(label: 'Paid', state: _StepState.done, caption: caption));
      } else {
        steps.add(const _Step(label: 'Paid', state: _StepState.upcoming, caption: 'Awaiting payment'));
      }
    }

    return steps;
  }

  @override
  Widget build(BuildContext context) {
    final steps = _buildSteps();
    if (steps.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < steps.length; i++) _stepRow(steps[i], isLast: i == steps.length - 1),
      ],
    );
  }

  Widget _stepRow(_Step step, {required bool isLast}) {
    final Color dotColor;
    final Color lineColor;
    IconData? icon;
    switch (step.state) {
      case _StepState.done:
        dotColor = AppColors.success;
        lineColor = AppColors.success;
        icon = Icons.check;
        break;
      case _StepState.current:
        dotColor = AppColors.orange;
        lineColor = AppColors.divider;
        icon = null;
        break;
      case _StepState.rejected:
        dotColor = AppColors.danger;
        lineColor = AppColors.divider;
        icon = Icons.close;
        break;
      case _StepState.upcoming:
        dotColor = AppColors.divider;
        lineColor = AppColors.divider;
        icon = null;
        break;
    }

    final labelColor = step.state == _StepState.upcoming ? AppColors.textSecondary : AppColors.textPrimary;

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              Container(
                width: 22,
                height: 22,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: step.state == _StepState.upcoming ? Colors.transparent : dotColor,
                  border: step.state == _StepState.upcoming ? Border.all(color: AppColors.divider, width: 2) : null,
                ),
                child: icon != null ? Icon(icon, size: 14, color: Colors.white) : null,
              ),
              if (!isLast) Expanded(child: Container(width: 2, color: lineColor)),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: isLast ? 0 : 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    step.label,
                    style: TextStyle(
                      fontWeight: step.state == _StepState.current ? FontWeight.w700 : FontWeight.w600,
                      color: labelColor,
                    ),
                  ),
                  if (step.caption != null && step.caption!.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      step.caption!,
                      style: TextStyle(
                        color: step.state == _StepState.rejected ? AppColors.danger : AppColors.textSecondary,
                        fontWeight: step.emphasizeCaption ? FontWeight.w700 : FontWeight.normal,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
