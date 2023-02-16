from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

def MinMax_scaler_data(X, X2, y):
    
    X = np.append(X, X2, axis=1)
    
#     X_max, X_min = np.amax(X, axis=0), np.amin(X, axis=0)
#     y_max, y_min = np.amax(y, axis=0), np.amin(y, axis=0)
    
#     x_scaled = (X - X_min) / (X_max - X_min)
#     y_scaled = (y - y_min) / (y_max - X_min)
    
    # MinMaxScaler dataset
    MinMaxSc = MinMaxScaler(feature_range=(0,1))
    x_scaled = MinMaxSc.fit_transform(X)
    y_scaled = MinMaxSc.fit_transform(y)
    
    return x_scaled, y_scaled

def Robust_scaler_data(X, X2, y):
    
    X = np.append(X, X2, axis=1)
    
#     X_mean, X_std = np.mean(X, axis=0), np.std(X, axis=0)
#     y_mean, y_std = np.mean(y, axis=0), np.std(y, axis=0)
    
#     # perform a robust scaler transform of the dataset
#     percen = 5
#     X_p1, X_p2 = np.percentile(X, percen, axis=0), np.percentile(X, 100-percen, axis=0)
#     y_p1, y_p2 = np.percentile(y, percen, axis=0), np.percentile(y, 100-percen, axis=0)
    
#     x_scaled = (X - X_mean) / (X_p2 - X_p1)
#     y_scaled = (y - y_mean) / (y_p2 - y_p1)
    
    RobustSc = RobustScaler(quantile_range=(percen, 100.0-percen))
    x_scaled = RobustSc.fit_transform(X)
    y_scaled = RobustSc.fit_transform(y)
    
    return x_scaled, y_scaled

def Standard_scaler_data(X, X2, y):
    
    X = np.append(X, X2, axis=1)
    
#     X_mean, X_std = np.mean(X, axis=0), np.std(X, axis=0)
#     y_mean, y_std = np.mean(y, axis=0), np.std(y, axis=0)
    
#     x_scaled = (X - X_mean) / X_std
#     y_scaled = (y - y_mean) / y_std
    
    StandardSc = StandardScaler()
    x_scaled = StandardSc.fit_transform(X)
    y_scaled = StandardSc.fit_transform(y)
    
    return x_scaled, y_scaled