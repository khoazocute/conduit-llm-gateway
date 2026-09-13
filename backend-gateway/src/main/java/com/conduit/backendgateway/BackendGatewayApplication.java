package com.conduit.backendgateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class BackendGatewayApplication {

	public static void main(String[] args) {
		SpringApplication.run(BackendGatewayApplication.class, args);
	}

}
