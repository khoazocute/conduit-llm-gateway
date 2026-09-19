package com.conduit.backendgateway.dto.purchase;

import com.conduit.backendgateway.dto.agent.AgentResponse;

/** One entry of the buyer's library: the agent they own plus the purchase that granted it. */
public record PurchasedAgentResponse(AgentResponse agent, AgentPurchaseResponse purchase) {
}
