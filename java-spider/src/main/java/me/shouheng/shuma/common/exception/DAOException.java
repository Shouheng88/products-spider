package me.shouheng.shuma.common.exception;

/**
 * DAO 异常封装
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019-08-01  21:19
 */
public class DAOException extends BizException {

    private static final String ENTITY_UPDATE_FAILED = "Failed to update entity";

    private static final String ENTITY_DELETE_FAILED = "Failed to delete entity";

    public DAOException() {
    }

    public DAOException(String message) {
        super(message);
    }

    public DAOException(String message, Throwable cause) {
        super(message, cause);
    }

    public DAOException(Throwable cause) {
        super(cause);
    }

    public DAOException(String message, Throwable cause, boolean enableSuppression, boolean writableStackTrace) {
        super(message, cause, enableSuppression, writableStackTrace);
    }

    public static <V> DAOException getUpdateException(V vo) {
        return new DAOException(ENTITY_UPDATE_FAILED + " : " + vo);
    }

    public static DAOException getDeleteException(long id) {
        return new DAOException(ENTITY_DELETE_FAILED + " : [" + + id + "]");
    }
}
