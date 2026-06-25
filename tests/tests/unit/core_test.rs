// tests/unit/core_test.rs
#[cfg(test)]
mod tests {
    use securellm_core::*;

    #[test]
    fn test_request_validation() {
        let req = ChatRequest {
            messages: vec![],
            model: "".to_string(),
        };
        assert!(req.validate().is_err());
    }

    #[test]
    fn test_error_handling() {
        let err = CoreError::ProviderError("timeout".into());
        assert!(err.is_retryable());
    }

    #[tokio::test]
    async fn test_provider_trait() {
        let provider = MockProvider::new();
        let result = provider.chat(valid_request()).await;
        assert!(result.is_ok());
    }
}
