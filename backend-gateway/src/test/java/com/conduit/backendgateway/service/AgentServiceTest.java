package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.enums.AgentStatus;
import com.conduit.backendgateway.domain.enums.UserRole;
import com.conduit.backendgateway.domain.enums.UserStatus;
import com.conduit.backendgateway.dto.agent.AgentResponse;
import com.conduit.backendgateway.dto.agent.CreateAgentRequest;
import com.conduit.backendgateway.dto.agent.RejectAgentRequest;
import com.conduit.backendgateway.dto.agent.UpdateAgentRequest;
import com.conduit.backendgateway.exception.ForbiddenActionException;
import com.conduit.backendgateway.exception.InvalidAgentStatusTransitionException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.AgentRepository;
import com.conduit.backendgateway.security.UserPrincipal;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;

/** TASK-52 + D8. AgentRepository la mock; saveAndFlush tra lai chinh agent. */
@ExtendWith(MockitoExtension.class)
class AgentServiceTest {

    private static final String SECRET = "you are a patient math tutor";

    @Mock private AgentRepository agentRepository;

    private AgentService agentService;
    private AdminAgentService adminAgentService;
    private UUID ownerId;
    private Agent agent;

    @BeforeEach
    void setUp() {
        agentService = new AgentService(agentRepository);
        adminAgentService = new AdminAgentService(agentRepository);
        ownerId = UUID.randomUUID();
        agent = new Agent();
        agent.setId(UUID.randomUUID());
        agent.setCreatorId(ownerId);
        agent.setTitle("Tutor");
        agent.setIntroduction("Public description");
        agent.setInstructions(SECRET);
        agent.setStatus(AgentStatus.published);
    }

    private void stubFind() {
        when(agentRepository.findById(agent.getId())).thenReturn(Optional.of(agent));
    }

    private void stubSave() {
        when(agentRepository.saveAndFlush(any(Agent.class))).thenAnswer(inv -> inv.getArgument(0));
    }

    private static UserPrincipal principal(UUID id, UserRole role) {
        return new UserPrincipal(id, "x@conduit.dev", role, UserStatus.active);
    }

    // ------------------------------------------------------------------ D8: ai thay instructions


    @Test
    void anonymousVisitor_getsPublicView() {
        stubFind();
        assertThat(agentService.getById(agent.getId(), null).instructions()).isNull();
    }

    @Test
    void buyerOrAnotherCreator_getsPublicView() {
        stubFind();
        assertThat(agentService.getById(agent.getId(), principal(UUID.randomUUID(), UserRole.user))
                .instructions()).isNull();
        assertThat(agentService.getById(agent.getId(), principal(UUID.randomUUID(), UserRole.creator))
                .instructions()).isNull();
    }

    @Test
    void owner_andAdmin_seeInstructions() {
        stubFind();
        assertThat(agentService.getById(agent.getId(), principal(ownerId, UserRole.creator))
                .instructions()).isEqualTo(SECRET);
        assertThat(agentService.getById(agent.getId(), principal(UUID.randomUUID(), UserRole.admin))
                .instructions()).isEqualTo(SECRET);
    }

    @Test
    void publicMarketplaceListing_neverCarriesInstructions() {
        when(agentRepository.findByStatus(any(), any())).thenReturn(new PageImpl<>(List.of(agent)));
        assertThat(agentService.listPublished(null, PageRequest.of(0, 10)).items())
                .allSatisfy(a -> assertThat(a.instructions()).isNull());
    }

    @Test
    void ownersOwnList_andAdminPendingList_carryInstructions() {
        when(agentRepository.findByCreatorId(any(), any())).thenReturn(new PageImpl<>(List.of(agent)));
        when(agentRepository.findByStatus(any(), any())).thenReturn(new PageImpl<>(List.of(agent)));
        assertThat(agentService.listMine(ownerId, null, PageRequest.of(0, 10)).items().get(0).instructions())
                .isEqualTo(SECRET);
        assertThat(adminAgentService.listPending(PageRequest.of(0, 10)).items().get(0).instructions())
                .isEqualTo(SECRET);
    }

    @Test
    void ownerView_carriesEmptyStringWhenUnset_soTheUiCanTellItFromThePublicView() {
        agent.setInstructions(null);
        assertThat(AgentResponse.withInstructions(agent).instructions()).isEqualTo("");
        assertThat(AgentResponse.from(agent).instructions()).isNull();
    }

    @Test
    void publicJson_hasNoInstructionsKeyAtAll() throws Exception {
        ObjectMapper json = new ObjectMapper().findAndRegisterModules();
        assertThat(json.writeValueAsString(AgentResponse.from(agent)))
                .doesNotContain("instructions").doesNotContain(SECRET);
        assertThat(json.writeValueAsString(AgentResponse.withInstructions(agent))).contains(SECRET);
    }

    // ------------------------------------------------------------------ create / update

    @Test
    void create_storesInstructions_andReturnsOwnerView() {
        stubSave();
        AgentResponse r = agentService.create(ownerId,
                new CreateAgentRequest("New", "intro", SECRET, null, 1000, 10));
        assertThat(r.instructions()).isEqualTo(SECRET);
        assertThat(r.status()).isEqualTo(AgentStatus.draft);
        assertThat(r.creatorId()).isEqualTo(ownerId);
    }

    @Test
    void update_byNonOwner_isForbidden_andNothingIsSaved() {
        agent.setStatus(AgentStatus.draft);
        stubFind();
        assertThatThrownBy(() -> agentService.update(agent.getId(), UUID.randomUUID(),
                new UpdateAgentRequest("Hacked", null, null, null, null)))
                .isInstanceOf(ForbiddenActionException.class);
        verify(agentRepository, never()).saveAndFlush(any());
    }

    @Test
    void update_onPublishedAgent_isRejected() {
        stubFind();
        assertThatThrownBy(() -> agentService.update(agent.getId(), ownerId,
                new UpdateAgentRequest("Changed", null, null, null, null)))
                .isInstanceOf(InvalidAgentStatusTransitionException.class);
    }

    @Test
    void update_withNullInstructions_keepsTheStoredOnes() {
        agent.setStatus(AgentStatus.draft);
        stubFind();
        stubSave();
        AgentResponse r = agentService.update(agent.getId(), ownerId,
                new UpdateAgentRequest("Renamed", null, null, null, null));
        assertThat(r.title()).isEqualTo("Renamed");
        assertThat(r.instructions()).isEqualTo(SECRET);
    }

    @Test
    void update_withNewInstructions_replacesThem() {
        agent.setStatus(AgentStatus.rejected);
        stubFind();
        stubSave();
        assertThat(agentService.update(agent.getId(), ownerId,
                new UpdateAgentRequest(null, null, "be concise", null, null)).instructions())
                .isEqualTo("be concise");
    }

    @Test
    void getById_unknownAgent_isNotFound() {
        UUID missing = UUID.randomUUID();
        when(agentRepository.findById(missing)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> agentService.getById(missing, null)).isInstanceOf(ResourceNotFoundException.class);
    }

    // ------------------------------------------------------------------ state machine

    @ParameterizedTest
    @EnumSource(value = AgentStatus.class, names = {"draft", "rejected", "unpublished"})
    void submit_fromSubmittableStatus_goesToPending_andClearsRejectReason(AgentStatus from) {
        agent.setStatus(from);
        agent.setRejectReason("old reason");
        stubFind();
        stubSave();
        AgentResponse r = agentService.submit(agent.getId(), ownerId);
        assertThat(r.status()).isEqualTo(AgentStatus.pending);
        assertThat(r.rejectReason()).isNull();
    }

    @ParameterizedTest
    @EnumSource(value = AgentStatus.class, names = {"pending", "published"})
    void submit_fromOtherStatus_isRejected(AgentStatus from) {
        agent.setStatus(from);
        stubFind();
        assertThatThrownBy(() -> agentService.submit(agent.getId(), ownerId))
                .isInstanceOf(InvalidAgentStatusTransitionException.class);
    }

    @Test
    void unpublish_onlyFromPublished_andOnlyByOwner() {
        stubFind();
        assertThatThrownBy(() -> agentService.unpublish(agent.getId(), UUID.randomUUID()))
                .isInstanceOf(ForbiddenActionException.class);

        stubSave();
        assertThat(agentService.unpublish(agent.getId(), ownerId).status()).isEqualTo(AgentStatus.unpublished);

        assertThatThrownBy(() -> agentService.unpublish(agent.getId(), ownerId))
                .isInstanceOf(InvalidAgentStatusTransitionException.class);
    }

    @Test
    void adminApproveAndReject_onlyWorkOnPendingAgents() {
        agent.setStatus(AgentStatus.pending);
        stubFind();
        stubSave();
        assertThat(adminAgentService.approve(agent.getId()).status()).isEqualTo(AgentStatus.published);

        // Da published -> khong duyet/tu choi lai duoc.
        assertThatThrownBy(() -> adminAgentService.reject(agent.getId(), new RejectAgentRequest("late")))
                .isInstanceOf(InvalidAgentStatusTransitionException.class);

        agent.setStatus(AgentStatus.pending);
        AgentResponse rejected = adminAgentService.reject(agent.getId(), new RejectAgentRequest("unsafe prompt"));
        assertThat(rejected.status()).isEqualTo(AgentStatus.rejected);
        assertThat(rejected.rejectReason()).isEqualTo("unsafe prompt");
    }
}
