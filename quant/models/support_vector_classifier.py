# ae_h - 2018/5/28

from datetime import datetime
from sklearn import preprocessing
from sklearn import svm
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split, GridSearchCV
from quant.dao.k_data_dao import k_data_dao
from quant.feature_utils.feature_collector import collect_features
from quant.log.quant_logging import quant_logging as logging
from quant.models.base_model import BaseModel
from sklearn.externals import joblib
from quant.dao.k_data_model_log_dao import k_data_model_log_dao

class SupportVectorClassifier(BaseModel):
    def training_model(self, code, data, features):
        model_name="support_vector_classifier"

        X_train, X_test, y_train, y_test = train_test_split(data[features], data['next_direction'], test_size=.3,
                                                            shuffle=False)

        tuned_parameters = [
            {'kernel': ['rbf'], 'gamma': [1e-3, 1e-4], 'C': [1, 10, 100, 1000]}
        ]

        # normalization
        X_train = preprocessing.scale(X_train)
        X_test = preprocessing.scale(X_test)

        # pca缩放
        pca = PCA(n_components=None)
        pca.fit(X_train)
        X_train = pca.transform(X_train)


        # # tsne缩放
        # X_train = TSNE(n_components=2, learning_rate=100).fit_transform(X_train)
        # X_test = TSNE(n_components=2, learning_rate=100).fit_transform(X_test)

        # 网格搜寻最优参数
        grid = GridSearchCV(svm.SVC(), tuned_parameters, cv=None, n_jobs=-1)
        grid.fit(X_train, y_train)

        logging.logger.debug(grid.best_estimator_)  # 训练的结果
        logging.logger.debug("Support Vector Classifier's best score: %.4f" % grid.best_score_)  # 训练的评分结果

        support_vector_classifier = grid.best_estimator_
        # 使用训练数据, 重新训练
        support_vector_classifier.fit(X_train, y_train)

        # 使用测试数据对模型进评平分
        y_test_pred = support_vector_classifier.predict(X_test)

        # 在测试集中的评分
        test_score = accuracy_score(y_test, y_test_pred)
        logging.logger.debug('test score: %.4f' % test_score)

        # 使用所有数据, 重新训练
        support_vector_classifier.fit(data[features], data['next_direction'])

        # 记录日志
        k_data_model_log_dao.insert(code=code, name=model_name
                                    , best_estimator=grid.best_estimator_,
                                    train_score=grid.best_score_, test_score=test_score)

        # 输出模型
        joblib.dump(support_vector_classifier, self.get_model_path(code, model_name))