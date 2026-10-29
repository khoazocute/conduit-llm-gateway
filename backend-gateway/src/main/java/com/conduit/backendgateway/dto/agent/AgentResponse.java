package com.conduit.backendgateway.dto.agent;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.enums.AgentStatus;
import com.conduit.backendgateway.domain.enums.AgentType;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record AgentResponse(
        UUID id,
        @JsonProperty("creator_id") UUID creatorId,
        String title,
        String introduction,
        // D8: CHI co gia tri trong withInstructions(); from() luon de null va NON_NULL an han
        // truong nay khoi JSON. Mac dinh an toan: quen loc thi ket qua la khong lo.
        @JsonInclude(JsonInclude.Include.NON_NULL) String instructions,
        @JsonProperty("agent_type") AgentType agentType,
        @JsonProperty("price_vnd") Integer priceVnd,
        @JsonProperty("default_credit_granted") Integer defaultCreditGranted,
        AgentStatus status,
        @JsonProperty("reject_reason") String rejectReason,
        @JsonProperty("created_at") Instant createdAt,
        @JsonProperty("updated_at") Instant updatedAt) {

    /** Ban CONG KHAI: khong bao gio co instructions. Dung cho cho, trang chi tiet, nguoi mua. */
    public static AgentResponse from(Agent agent) {
        return build(agent, null);
    }

    /**
     * Ban cho CHU AGENT hoac ADMIN: kem instructions. Chi goi o cho da xac nhan quyen
     * (requireOwnership, route /admin/**, hoac getById da kiem nguoi goi).
     */
    public static AgentResponse withInstructions(Agent agent) {
        // Luon co truong (rong -> "") de frontend phan biet duoc "ban cho chu agent, chua dat
        // instructions" voi "ban cong khai, khong duoc xem". Neu khong, trang sua agent nhan
        // ban cong khai se tuong instructions rong va GHI DE mat system prompt khi luu.
        return build(agent, agent.getInstructions() == null ? "" : agent.getInstructions());
    }

    private static AgentResponse build(Agent agent, String instructions) {
        return new AgentResponse(
                agent.getId(),
                agent.getCreatorId(),
                agent.getTitle(),
                agent.getIntroduction(),
                instructions,
                agent.getAgentType(),
                agent.getPriceVnd(),
                agent.getDefaultCreditGranted(),
                agent.getStatus(),
                agent.getRejectReason(),
                agent.getCreatedAt(),
                agent.getUpdatedAt());
    }
}
