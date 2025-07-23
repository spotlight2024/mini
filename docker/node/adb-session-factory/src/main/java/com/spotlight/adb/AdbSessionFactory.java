package com.spotlight.adb;

import org.openqa.selenium.Capabilities;
import org.openqa.selenium.Platform;
import org.openqa.selenium.WebDriverException;
import org.openqa.selenium.grid.config.Config;
import org.openqa.selenium.grid.data.CreateSessionRequest;
import org.openqa.selenium.grid.node.ActiveSession;
import org.openqa.selenium.grid.node.SessionFactory;
import org.openqa.selenium.internal.Either;
import org.openqa.selenium.remote.DesiredCapabilities;
import org.openqa.selenium.remote.http.HttpClient;
import org.openqa.selenium.remote.tracing.Tracer;

import java.io.IOException;
import java.util.Map;
import java.util.logging.Logger;

public class AdbSessionFactory implements SessionFactory {
    private final Tracer tracer;
    private final HttpClient.Factory clientFactory;
    private final SessionFactory delegateFactory; // 委托给原生SessionFactory

    private static final Logger LOG = Logger.getLogger(AdbSessionFactory.class.getName());

    public AdbSessionFactory(Tracer tracer, HttpClient.Factory clientFactory, SessionFactory delegateFactory) {
        this.tracer = tracer;
        this.clientFactory = clientFactory;
        this.delegateFactory = delegateFactory;
    }

    /**
     * 静态工厂方法，符合Selenium Grid SPI要求
     * @param config 配置对象
     * @param stereotype 能力配置
     * @return SessionFactory实例
     */
    public static SessionFactory create(Config config, Capabilities stereotype) {
        LOG.info("[AdbSessionFactory] create() called with stereotype: " + stereotype);
        
        // 创建Tracer和HttpClient.Factory
        // 在实际使用中，Tracer应该从config中获取，这里简化处理
        Tracer tracer = null; // 使用null，让Selenium Grid处理Tracer
        HttpClient.Factory httpClientFactory = HttpClient.Factory.createDefault();
        
        // 这里应该创建或获取原生的SessionFactory
        // 由于Selenium Grid的复杂性，这里简化处理
        // 实际使用时，您可能需要通过其他方式获取原生工厂
        
        return new AdbSessionFactory(tracer, httpClientFactory, null);
    }

    @Override
    public Capabilities getStereotype() {
        LOG.info("[AdbSessionFactory] getStereotype() called, returning chrome capability");
        // 返回支持ADB的Chrome能力配置
        return new DesiredCapabilities("chrome", "138", Platform.valueOf("linux"));
    }

    @Override
    public boolean test(Capabilities capabilities) {
        boolean match = "chrome".equalsIgnoreCase(capabilities.getBrowserName())
            && capabilities.asMap().containsKey("se:adbDeviceId");
        LOG.info("[AdbSessionFactory] test() called, browserName=" + capabilities.getBrowserName() 
            + ", adbDeviceId=" + capabilities.asMap().get("se:adbDeviceId") + ", match=" + match);
        return match;
    }

    @Override
    public Either<WebDriverException, ActiveSession> apply(CreateSessionRequest req) {
        LOG.info("[AdbSessionFactory] apply() called, processing new session request");
        
        Map<String, Object> caps = req.getDesiredCapabilities().asMap();
        String adbDeviceId = (String) caps.get("se:adbDeviceId");
        
        if (adbDeviceId != null && !adbDeviceId.isEmpty()) {
            LOG.info("[AdbSessionFactory] adbDeviceId found: " + adbDeviceId + ", executing adb connect...");
            try {
                // 执行adb connect命令
                Process process = Runtime.getRuntime().exec("adb connect " + adbDeviceId);
                int exitCode = process.waitFor();
                LOG.info("[AdbSessionFactory] adb connect exit code: " + exitCode);
                
                if (exitCode != 0) {
                    throw new WebDriverException("ADB连接失败，退出码: " + exitCode);
                }
                
                // 等待设备连接稳定
                Thread.sleep(2000);
                
            } catch (IOException | InterruptedException e) {
                LOG.severe("[AdbSessionFactory] adb connect failed: " + e.getMessage());
                throw new WebDriverException("ADB连接失败: " + adbDeviceId, e);
            }
        } else {
            LOG.info("[AdbSessionFactory] adbDeviceId is null or empty, skipping adb connect.");
        }
        
        // 如果有委托工厂，使用委托工厂创建会话
        if (delegateFactory != null) {
            LOG.info("[AdbSessionFactory] delegating to native SessionFactory");
            return delegateFactory.apply(req);
        }
        
        // 如果没有委托工厂，抛出异常
        throw new UnsupportedOperationException(
            "AdbSessionFactory需要委托给原生SessionFactory。请确保正确配置了委托工厂。");
    }
}