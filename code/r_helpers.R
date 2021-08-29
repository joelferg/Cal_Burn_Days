require(fixest)
require(dplyr)

#Triangle Kernel
tri_k <- function(x){
  out <- (1-abs(x))*(abs(x)<=1)
  return(out)
}

# Imbens & Kalyanaraman 2012 optimal bandwidth + local linear est.
IK2012 <- function(df,running,outcome){
  df <- as.data.frame(df)
  run_mean <- df[[running]]
  Sx2 <- sum((df[[running]]-mean(df[[running]]))^2)/(nrow(df)-1)
  h1 <- 1.84*sqrt(Sx2)*(nrow(df)^(-1/5))
  Nh1_neg <- nrow(df[df[[running]]<0&abs(df[[running]])<=h1,])
  Nh1_pos <- nrow(df[df[[running]]>=0&abs(df[[running]])<=h1,])
  Ybar_h1_neg <- mean(df[df[[running]]<0&abs(df[[running]]<=h1),outcome])
  Ybar_h1_pos <- mean(df[df[[running]]>=0&abs(df[[running]]<=h1),outcome])
  f_hat_c <- (Nh1_neg+Nh1_pos)/(2*nrow(df)*h1)
  sigma2_neg_c <- sum((df[df[[running]]<0&abs(df[[running]])<=h1,outcome]-Ybar_h1_neg)^2)/(Nh1_neg-1)
  sigma2_pos_c <- sum((df[df[[running]]>=0&abs(df[[running]])<=h1,outcome]-Ybar_h1_neg)^2)/(Nh1_neg-1)
  
  df[,'above'] <- df[[running]] >= 0
  
  o3poly_fml <- formula(
    paste(outcome,
          paste('above',running,paste0(running,"^2"),paste0(running,"^3"),sep="+"),
          sep="~")
  )
  
  o3poly <- feols(o3poly_fml,
                  data=df)
  m3_hat_c <- 6*o3poly$coefficients[[5]]
  h2_pos <- 3.65*(sigma2_pos_c/(f_hat_c*(m3_hat_c^2)))^(1/7)*(nrow(df[df[[running]]>=0,])^(-1/7))
  h2_neg <- 3.65*(sigma2_neg_c/(f_hat_c*(m3_hat_c^2)))^(1/7)*(nrow(df[df[[running]]<0,])^(-1/7))
  
  df_2pos <- df[abs(df[[running]])<=h2_pos&df[[running]]>=0,]
  q2_fml <- formula(paste(outcome,"~",running,"+",running,"^2"))
  q2_pos <- feols(q2_fml,
                  data=df_2pos)
  m2_pos_hat <- q2_pos$coefficients[[3]]
  
  
  df_2neg <- df[abs(df[[running]])<=h2_pos&df[[running]]<0,]
  if (var(df[df[[running]]<0,outcome])!=0){
    q2_neg <- feols(q2_fml,
                    data=df_2neg)
    m2_neg_hat <- q2_neg$coefficients[[3]]
  } else{
    m2_neg_hat <- 0
  }
  
  r_pos_hat <- (2160*sigma2_pos_c)/(nrow(df_2pos)*(h2_pos^4))
  r_neg_hat <- (2160*sigma2_neg_c)/(nrow(df_2neg)*(h2_neg^4))
  
  h_opt_hat <- 3.4375*((sigma2_neg_c+sigma2_pos_c)/(f_hat_c*((m2_pos_hat-m2_neg_hat)^2+(r_pos_hat+r_neg_hat))))^(1/5)*(nrow(df))^(-1/5)
  
  df[,'kXc'] <- sapply(df[[running]]/h_opt_hat,tri_k)
  W_pos <- diag(df[df[[running]]>=0,'kXc'])
  W_neg <- diag(df[df[[running]]<0,'kXc'])
  
  X_pos <- cbind(matrix(1,nrow(df[df[[running]]>=0,]),1),as.matrix(df[df[[running]]>=0,running]))
  X_neg <- cbind(matrix(1,nrow(df[df[[running]]<0,]),1),as.matrix(df[df[[running]]<0,running]))
  
  Y_pos <- as.matrix(df[df[[running]]>=0,outcome])
  Y_neg <- as.matrix(df[df[[running]]<0,outcome])
  
  m_c_pos <- solve(t(X_pos)%*%W_pos%*%X_pos)%*%(t(X_pos)%*%W_pos%*%Y_pos)
  m_c_neg <- solve(t(X_neg)%*%W_neg%*%X_neg)%*%(t(X_neg)%*%W_neg%*%Y_neg)
  tau_hat <- (m_c_pos-m_c_neg)[1,1]
  
  out <- list('h_opt' = h_opt_hat,
              'tau' = tau_hat)
  
  return(out)
  
}


# McCrary Test

mccrary <- function(df,running,outcome){
  df <- as.data.frame(df)
  b_hat <- 2*sd(df[[running]])*(nrow(df)^(-1/2))
  g_min <- floor(min(df[[running]])/b_hat)*b_hat+(b_hat/2)
  g_max <- floor(max(df[[running]])/b_hat)*b_hat+(b_hat/2)
  all_gs <- round(data.frame(g=seq(g_min,g_max,b_hat)),2)
  df[,'g'] <- round(floor(df[[running]]/b_hat)*b_hat+(b_hat/2),2)
  mc_hist <- df %>%
    group_by(g) %>%
    summarise(Y=n(),
              across(outcome,function(x) mean(x,na.rm=T),.names="outcome")) %>%
    mutate(Y=Y/(nrow(df)*b_hat)) %>%
    right_join(all_gs,by="g")
  mc_hist$Y[is.na(mc_hist$Y)] <- 0
  
  dense_hist <- ggplot(data=mc_hist)+
    geom_point(mapping=aes(x=g,y=Y))
  
  mc_hist_l <- mc_hist %>%
    filter(g < 0)
  
  left_o4 <- feols(Y~g+g^2+g^3+g^4,
                   data=mc_hist_l)
  mc_hist_l$f2 <- 2*left_o4$coefficients[[3]]+6*mc_hist_l$g*left_o4$coefficients[[4]]+
    12*(mc_hist_l$g^2)*left_o4$coefficients[[5]]
  
  h_hat_l <- 3.348*(-1*(left_o4$ssr/left_o4$nobs)*min(mc_hist_l$g)/sum(mc_hist_l$f2^2))^(1/5)
  
  mc_hist_r <- mc_hist %>%
    filter(g >= 0)
  
  right_o4 <- feols(Y~g+g^2+g^3+g^4,
                    data=mc_hist_r)
  mc_hist_r$f2 <- 2*right_o4$coefficients[[3]]+6*mc_hist_r$g*right_o4$coefficients[[4]]+
    12*(mc_hist_r$g^2)*right_o4$coefficients[[5]]
  h_hat_r <- 3.348*((right_o4$ssr/right_o4$nobs)*max(mc_hist_r$g)/sum(mc_hist_r$f2^2))^(1/5)
  
  h_hat <- mean(c(h_hat_r,h_hat_l))
  
  bandwidth_dense <- ggplot(data=mc_hist[abs(mc_hist$g)<h_hat,])+
    geom_point(mapping=aes(x=g,y=Y)) +
    geom_vline(aes(xintercept=0),color="red")+
    scale_x_continuous(name="Allocation Equation",breaks=seq(-4000,4000,1000))+
    scale_y_continuous(name="Density")
  
  out_hist <- ggplot(data=mc_hist[abs(mc_hist$g)<h_hat,])+
    geom_point(mapping=aes(x=g,y=outcome))
  
  out <- list(
    'dense_hist' = dense_hist,
    'bandwidth_dense' = bandwidth_dense,
    'out_hist' = out_hist
  )
  return(out)
  
}