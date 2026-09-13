package com.conduit.backendgateway.security;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.exception.InvalidOrExpiredTokenException;
import com.conduit.backendgateway.repository.UserRepository;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Reads the (header-only) access token. Refresh tokens are cookie/body-only and are handled
 * entirely inside AuthController/AuthService, never through this filter.
 */
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtService jwtService;
    private final UserRepository userRepository;

    public JwtAuthenticationFilter(JwtService jwtService, UserRepository userRepository) {
        this.jwtService = jwtService;
        this.userRepository = userRepository;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith(BEARER_PREFIX)) {
            filterChain.doFilter(request, response);
            return;
        }

        String token = header.substring(BEARER_PREFIX.length());
        try {
            Jws<Claims> claims = jwtService.parseAndValidate(token);
            if (!jwtService.isAccessToken(claims)) {
                throw new InvalidOrExpiredTokenException("Not an access token");
            }

            UUID userId = jwtService.extractUserId(claims);
            User user = userRepository.findById(userId).orElse(null);
            if (user != null) {
                UserPrincipal principal = UserPrincipal.fromUser(user);
                var authentication = new UsernamePasswordAuthenticationToken(
                        principal, null, principal.getAuthorities());
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        } catch (InvalidOrExpiredTokenException ex) {
            SecurityContextHolder.clearContext();
        }

        filterChain.doFilter(request, response);
    }
}
