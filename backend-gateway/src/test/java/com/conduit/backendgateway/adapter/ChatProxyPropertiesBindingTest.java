package com.conduit.backendgateway.adapter;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/**
 * TASK-51: application.yml THAT phai bind duoc proxy-default-models. Sai ten khoa thi Spring bo qua
 * khong bao loi, effectiveDefaultModel() roi ve gpt-4o-mini, va chat thuong LAI KHONG qua
 * conduit-pool - ma routing_decisions khong phan biet duoc (ca hai duong deu ghi gpt-4o-mini).
 *
 * Chay khong dat CHAT_DEFAULT_MODEL / CHAT_ACTIVE_PROXY (mac dinh litellm).
 */
@SpringBootTest(properties = {"app.chat.active-proxy=litellm", "app.chat.default-model="})
class ChatProxyPropertiesBindingTest {

    @Autowired
    private ChatProxyProperties properties;

    @Test
    void realConfigSendsLitellmChatThroughTheCostRoutedPool() {
        assertThat(properties.getProxyDefaultModels()).containsEntry("litellm", "conduit-pool");
        assertThat(properties.effectiveDefaultModel()).isEqualTo("conduit-pool");
    }

    @Test
    void realConfigSendsMaxTokensAndTemperature() {
        assertThat(properties.getMaxTokens()).isEqualTo(1024);
        assertThat(properties.getTemperature()).isZero();
    }
}
